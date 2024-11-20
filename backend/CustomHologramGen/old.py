import time
import cupy as cp
import cv2
import numpy as np

def gerchberg_saxton_cupy(target_intensity, iterations=10):
    amplitude = cp.sqrt(target_intensity)
    phase = cp.random.rand(*amplitude.shape) * 2 * cp.pi

    for _ in range(iterations):
        field = amplitude * cp.exp(1j * phase)
        fft_field = cp.fft.fft2(field)
        fft_phase = cp.angle(fft_field)
        constrained_field = amplitude * cp.exp(1j * fft_phase)
        ifft_field = cp.fft.ifft2(constrained_field)
        phase = cp.angle(ifft_field)

    hologram = phase
    return hologram

class HologramGeneratorCupy:
    def __init__(self):
        self.width = 0
        self.height = 0
        self.depth = 0
        self.iterations = 0
        self.rgb = False
        self.affine_params = None

    def Initialize_HologramGenerator(self, width, height, depth, iterations, RGB):
        self.width = width
        self.height = height
        self.depth = depth
        self.iterations = iterations
        self.rgb = bool(RGB)
        return 0

    def CalculateAffinePolynomials(self,
                                   SLM_X_0, SLM_Y_0, CAM_X_0, CAM_Y_0,
                                   SLM_X_1, SLM_Y_1, CAM_X_1, CAM_Y_1,
                                   SLM_X_2, SLM_Y_2, CAM_X_2, CAM_Y_2):
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
        return 0

    def Generate_Hologram(self, WFC, x_spots, y_spots, z_spots, I_spots, N_spots, ApplyAffine):
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

if __name__ == '__main__':
    height = 1152
    width = 1920
    depth = 8
    iterations = 10
    is_rgb = False
    is_apply_affine = True

    for i in range(100):
        n = 200
        x_array = cp.random.uniform(0, width, n).astype(cp.float32)
        y_array = cp.random.uniform(0, height, n).astype(cp.float32)
        z_array = cp.zeros(n, dtype=cp.float32)

        # x_array = cp.array([-10, 10], dtype=np.float32)
        # y_array = cp.zeros(n, dtype=np.float32)
        # z_array = cp.zeros(n, dtype=np.float32)
        

        intensity_array = cp.ones(n, dtype=cp.float32)

        WFC = cp.zeros((height, width), dtype=cp.float32)

        holo_gen = HologramGeneratorCupy()
        holo_gen.Initialize_HologramGenerator(width, height, depth, iterations, is_rgb)
        holo_gen.CalculateAffinePolynomials(
            SLM_X_0=10, SLM_Y_0=10, CAM_X_0=10, CAM_Y_0=10,
            SLM_X_1=-10, SLM_Y_1=-10, CAM_X_1=-10, CAM_Y_1=-10,
            SLM_X_2=10, SLM_Y_2=-10, CAM_X_2=10, CAM_Y_2=-10
        )

        start_time = time.time()
        hologram_image = holo_gen.Generate_Hologram(
            WFC, x_array, y_array, z_array, intensity_array, n, is_apply_affine
        )
        print("Time taken to generate hologram:", time.time() - start_time)

        hologram_image = (hologram_image - cp.min(hologram_image)) / (cp.max(hologram_image) - cp.min(hologram_image)) * 255
        hologram_image = hologram_image.astype(cp.uint8)
        hologram_image = cp.asnumpy(hologram_image)


        start_time = time.time()

        cv2.imwrite(f"./imgs/hologram_image_{i}.png", hologram_image)

        print("Time taken to save image:", time.time() - start_time)



    print("Done")