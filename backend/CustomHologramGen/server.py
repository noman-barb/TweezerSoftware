import grpc
from concurrent import futures
import time
import hologram_pb2
import hologram_pb2_grpc
import numpy as np
import cupy as cp


# works






cuda_code = r"""
extern "C" __global__
void update_phase(const float* amplitude, const float* fft_real, const float* fft_imag,
                  float* output_phase, int rows, int cols) {
    int i = blockIdx.y * blockDim.y + threadIdx.y;
    int j = blockIdx.x * blockDim.x + threadIdx.x;

    if (i < rows && j < cols) {
        int idx = i * cols + j;

        // Calculate phase from real and imaginary parts
        float phase = atan2f(fft_imag[idx], fft_real[idx]);
        output_phase[idx] = phase;
    }
}
"""


def gerchberg_saxton_cupy(target_intensity, iterations):
    # Initialize amplitude and phase
    amplitude = cp.sqrt(target_intensity).astype(cp.float32)
    phase = (cp.random.rand(*amplitude.shape) * 2 * cp.pi).astype(cp.float32)

    # Allocate space for FFT components and output phase
    fft_real = cp.zeros_like(amplitude, dtype=cp.float32)
    fft_imag = cp.zeros_like(amplitude, dtype=cp.float32)
    output_phase = cp.zeros_like(amplitude, dtype=cp.float32)

    # Compile CUDA kernel
    update_phase_kernel = cp.RawKernel(cuda_code, "update_phase")

    # Define CUDA grid and block sizes
    threads_per_block = (16, 16)
    blocks_per_grid_x = (amplitude.shape[1] + threads_per_block[0] - 1) // threads_per_block[0]
    blocks_per_grid_y = (amplitude.shape[0] + threads_per_block[1] - 1) // threads_per_block[1]
    blocks_per_grid = (blocks_per_grid_x, blocks_per_grid_y)

    for _ in range(iterations):
        # Perform FFT
        field = amplitude * cp.exp(1j * phase)
        fft_field = cp.fft.fft2(field)
        fft_real[:] = cp.real(fft_field)
        fft_imag[:] = cp.imag(fft_field)

        # Launch CUDA kernel
        update_phase_kernel(
            (blocks_per_grid[0], blocks_per_grid[1]), threads_per_block,
            (amplitude, fft_real, fft_imag, output_phase, amplitude.shape[0], amplitude.shape[1])
        )

        # Update phase
        phase[:] = output_phase[:]

    hologram = phase
    return hologram




# def gerchberg_saxton_cupy(target_intensity, iterations):
#     amplitude = cp.sqrt(target_intensity)
#     phase = cp.random.rand(*amplitude.shape) * 2 * cp.pi

#     for _ in range(iterations):
#         field = amplitude * cp.exp(1j * phase)
#         fft_field = cp.fft.fft2(field)
#         fft_phase = cp.angle(fft_field)
#         constrained_field = amplitude * cp.exp(1j * fft_phase)
#         ifft_field = cp.fft.ifft2(constrained_field)
#         phase = cp.angle(ifft_field)

#     hologram = phase
#     return hologram




class HologramGeneratorCupy:
    def __init__(self):
        self.width = 0
        self.height = 0
        self.depth = 0
        self.iterations = 0
        self.rgb = False
        self.affine_params = None
        self.stream = cp.cuda.Stream(non_blocking=True)

    def Initialize_HologramGenerator(self, width, height, depth, iterations, RGB):
        self.width = width
        self.height = height
        self.depth = depth
        self.iterations = iterations
        self.rgb = bool(RGB)

    def CalculateAffinePolynomials(self,
                                   SLM_X_0, SLM_Y_0, CAM_X_0, CAM_Y_0,
                                   SLM_X_1, SLM_Y_1, CAM_X_1, CAM_Y_1,
                                   SLM_X_2, SLM_Y_2, CAM_X_2, CAM_Y_2):
        with self.stream:
            A = cp.array([
                [SLM_X_0, SLM_Y_0, 1],
                [SLM_X_1, SLM_Y_1, 1],
                [SLM_X_2, SLM_Y_2, 1]
            ], dtype=cp.float32)
            Bx = cp.array([CAM_X_0, CAM_X_1, CAM_X_2], dtype=cp.float32)
            By = cp.array([CAM_Y_0, CAM_Y_1, CAM_Y_2], dtype=cp.float32)

            affine_x = cp.linalg.solve(A, Bx)
            affine_y = cp.linalg.solve(A, By)
            self.affine_params = (affine_x, affine_y)

    def Generate_Hologram(self, WFC, x_spots, y_spots, z_spots, I_spots, N_spots, ApplyAffine):
        with self.stream:
            if ApplyAffine and self.affine_params:
                affine_x, affine_y = self.affine_params
                x = affine_x[0] * x_spots + affine_x[1] * y_spots + affine_x[2]
                y = affine_y[0] * x_spots + affine_y[1] * y_spots + affine_y[2]
            else:
                x = x_spots
                y = y_spots

            x_idx = cp.clip(x.astype(cp.int32), 0, self.width - 1)
            y_idx = cp.clip(y.astype(cp.int32), 0, self.height - 1)

            hologram = cp.zeros((self.height, self.width), dtype=cp.float32)
            cp.add.at(hologram, (y_idx, x_idx), I_spots)

            if WFC is not None:
                hologram += WFC

            hologram /= cp.max(hologram)

            gs_hologram = gerchberg_saxton_cupy(hologram, iterations=self.iterations)
            return gs_hologram

# Ensure to use the stream in the servicer as well
class HologramGeneratorCupyServicer(hologram_pb2_grpc.HologramGeneratorServiceServicer):
    def __init__(self):
        self.total_data_received = 0  # in bytes
        self.total_data_sent = 0      # in bytes
        self.total_time_spent = 0     # in seconds
        self.request_count = 0

    def GenerateHologram(self, request, context):
        self.request_count += 1
        receive_start_time = time.time()

        # print(f"Received request with {request.height}x{request.width}x{request.depth} hologram")

        # Calculate data received size
        data_received = len(request.x_array) + len(request.y_array) + len(request.z_array) + len(request.intensity_array)
        self.total_data_received += data_received

        # Start processing timer
        start_time = time.time()

        height = request.height
        width = request.width
        depth = request.depth
        iterations = request.iterations
        is_rgb = request.is_rgb
        is_apply_affine = request.is_apply_affine

        x_array = cp.frombuffer(request.x_array, dtype=cp.float32)
        y_array = cp.frombuffer(request.y_array, dtype=cp.float32)
        z_array = cp.frombuffer(request.z_array, dtype=cp.float32)
        intensity_array = cp.frombuffer(request.intensity_array, dtype=cp.float32)

        n = x_array.size

        WFC = cp.zeros((height, width), dtype=cp.float32)

        holo_gen = HologramGeneratorCupy()
        holo_gen.Initialize_HologramGenerator(width, height, depth, iterations, is_rgb)
        holo_gen.CalculateAffinePolynomials(
            SLM_X_0=request.SLM_X_0, SLM_Y_0=request.SLM_Y_0, CAM_X_0=request.CAM_X_0, CAM_Y_0=request.CAM_Y_0,
            SLM_X_1=request.SLM_X_1, SLM_Y_1=request.SLM_Y_1, CAM_X_1=request.CAM_X_1, CAM_Y_1=request.CAM_Y_1,
            SLM_X_2=request.SLM_X_2, SLM_Y_2=request.SLM_Y_2, CAM_X_2=request.CAM_X_2, CAM_Y_2=request.CAM_Y_2
        )

        hologram_image = holo_gen.Generate_Hologram(
            WFC, x_array, y_array, z_array, intensity_array, n, is_apply_affine
        )

        hologram_image = (hologram_image - cp.min(hologram_image)) / (cp.max(hologram_image) - cp.min(hologram_image)) * 255
        hologram_image = hologram_image.astype(cp.uint8)
        hologram_image_np = hologram_image.get()
        hologram_image_bytes = hologram_image_np.tobytes()

        # Calculate data sent size
        data_sent = len(hologram_image_bytes)
        self.total_data_sent += data_sent

        # End processing timer
        end_time = time.time()
        processing_time = end_time - start_time
        self.total_time_spent += processing_time

        print(f"Generated hologram in {processing_time:.2f} seconds")

        # Log speeds every 10 requests
        if self.request_count % 10 == 0:
            # Convert bytes to bits and calculate Mbps
            # Calculate MBps
            total_data_received_mb = self.total_data_received / 1e6
            total_data_sent_mb = self.total_data_sent / 1e6
            data_receive_speed_mbps = total_data_received_mb / self.total_time_spent
            data_send_speed_mbps = total_data_sent_mb / self.total_time_spent

            print(f"\n\nAverage data receive speed over last {self.request_count} requests: {data_receive_speed_mbps:.2f} Mbps")
            print(f"\n\nAverage data send speed over last {self.request_count} requests: {data_send_speed_mbps:.2f} Mbps")

            # Reset counters
            self.total_data_received = 0
            self.total_data_sent = 0
            self.total_time_spent = 0
            self.request_count = 0

        response = hologram_pb2.HologramResponse(
            hologram_image=hologram_image_bytes,
            height=height,
            width=width
        )
        return response

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    hologram_pb2_grpc.add_HologramGeneratorServiceServicer_to_server(
        HologramGeneratorCupyServicer(), server
    )
    server.add_insecure_port('[::]:50051')
    server.start()
    print('Server started. Listening on port 50051.')
    try:
        while True:
            time.sleep(99999)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()