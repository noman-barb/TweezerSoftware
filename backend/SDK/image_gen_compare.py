import os
import time
import numpy as np
import threading
from threading import Lock
import multiprocessing
import cv2
import cupy as cp





def gerchberg_saxton_cupy(target_intensity, iterations=10):
    """
    Implements the Gerchberg-Saxton algorithm using CuPy to generate a hologram.
    
    Parameters:
        target_intensity (np.ndarray): 2D array of target intensity values.
        iterations (int): Number of iterations for the algorithm.
    
    Returns:
        np.ndarray: Phase-only hologram (on CPU).
    """
    # Move target intensity to GPU
    start_time = time.time()
    target_intensity = cp.array(target_intensity, dtype=cp.float32)
    print("Time taken to move to gpu:", time.time() - start_time)
    amplitude = cp.sqrt(target_intensity)
    phase = cp.random.rand(*amplitude.shape) * 2 * cp.pi  # Random initial phase

    for _ in range(iterations):
        # Forward Fourier Transform
        field = amplitude * cp.exp(1j * phase)
        fft_field = cp.fft.fft2(field)
        
        # Enforce magnitude constraint
        fft_phase = cp.angle(fft_field)
        constrained_field = amplitude * cp.exp(1j * fft_phase)
        
        # Inverse Fourier Transform
        ifft_field = cp.fft.ifft2(constrained_field)
        phase = cp.angle(ifft_field)


    start_time = time.time()
    hologram = cp.asnumpy(phase)  # Return phase-only hologram to CPU
    print("Time taken to move from gpu:", time.time() - start_time)
    return hologram


# def gerchberg_saxton_numpy(target_intensity, iterations=10):
#     """
#     Implements the Gerchberg-Saxton algorithm using NumPy to generate a hologram.
    
#     Parameters:
#         target_intensity (np.ndarray): 2D array of target intensity values.
#         iterations (int): Number of iterations for the algorithm.
    
#     Returns:
#         np.ndarray: Phase-only hologram.
#     """
#     amplitude = np.sqrt(target_intensity)
#     phase = np.random.rand(*amplitude.shape) * 2 * np.pi  # Random initial phase

#     for _ in range(iterations):

#         # Forward Fourier Transform
#         field = amplitude * np.exp(1j * phase)
#         fft_field = np.fft.fft2(field)
        
#         # Enforce magnitude constraint
#         fft_phase = np.angle(fft_field)
#         constrained_field = amplitude * np.exp(1j * fft_phase)
        
#         # Inverse Fourier Transform
#         ifft_field = np.fft.ifft2(constrained_field)
#         phase = np.angle(ifft_field)

       
    
#     return phase





class HologramGeneratorNumpy:
    def __init__(self):
        self.width = 0
        self.height = 0
        self.depth = 0
        self.iterations = 0
        self.rgb = False
        self.affine_params = None
    
    def Initialize_HologramGenerator(self, width, height, depth, iterations, RGB):
        """
        Initializes the hologram generator with the given parameters.
        """
        self.width = width
        self.height = height
        self.depth = depth
        self.iterations = iterations
        self.rgb = bool(RGB)
        return 0  # Return success

    def CalculateAffinePolynomials(self, 
                                   SLM_X_0, SLM_Y_0, CAM_X_0, CAM_Y_0,
                                   SLM_X_1, SLM_Y_1, CAM_X_1, CAM_Y_1,
                                   SLM_X_2, SLM_Y_2, CAM_X_2, CAM_Y_2):
        """
        Calculates the affine transformation coefficients based on calibration points.
        """
        A = np.array([
            [SLM_X_0, SLM_Y_0, 1],
            [SLM_X_1, SLM_Y_1, 1],
            [SLM_X_2, SLM_Y_2, 1]
        ])
        Bx = np.array([CAM_X_0, CAM_X_1, CAM_X_2])
        By = np.array([CAM_Y_0, CAM_Y_1, CAM_Y_2])
        
        affine_x = np.linalg.solve(A, Bx)
        affine_y = np.linalg.solve(A, By)
        self.affine_params = (affine_x, affine_y)
        return 0  # Return success

    def Generate_Hologram(self, WFC, x_spots, y_spots, z_spots, I_spots, N_spots, ApplyAffine):
        """
        Generates a hologram based on the given inputs.
        """
        # Initialize hologram array
        hologram = np.zeros((self.height, self.width), dtype=np.float32)
        for i in range(N_spots):
            x, y = x_spots[i], y_spots[i]
            intensity = I_spots[i]
            
            if ApplyAffine and self.affine_params:
                affine_x, affine_y = self.affine_params
                x = affine_x[0] * x + affine_x[1] * y + affine_x[2]
                y = affine_y[0] * x + affine_y[1] * y + affine_y[2]
            
            # Map spots into the hologram array
            x_idx = int(np.clip(x, 0, self.width - 1))
            y_idx = int(np.clip(y, 0, self.height - 1))
            hologram[y_idx, x_idx] += intensity
        
        # Add wavefront correction (WFC) if provided
        if WFC is not None:
            hologram += WFC.reshape(hologram.shape)
        
        # Normalize hologram
        hologram /= np.max(hologram)
       
        # Apply the Gerchberg-Saxton algorithm
        start_time = time.time()
        gs_hologram = gerchberg_saxton_cupy(hologram, iterations=self.iterations)
        print("gs algo:", time.time() - start_time)
    
        return gs_hologram

        






if __name__ == '__main__':

    


   
    height = 1152
    width = 1920
    depth = 8
    Bytes = depth // 8
    center_x = width // 2
    center_y = height // 2


    ############################################################################################################################################################################
   


    hologram_image = np.zeros([width * height * Bytes], np.uint8, 'C')
    hologram_image_1 = np.zeros([height, width, Bytes], np.uint8, 'C')
    WFC = np.zeros([width * height * Bytes], np.uint8, 'C')

    n = 100
    x_array = np.random.uniform(0, width, n).astype(np.float32)
    y_array = np.random.uniform(0, height, n).astype(np.float32)
    z_array = np.zeros(n, dtype=np.float32)

    x_array = np.array([-10, 10], dtype=np.float32)
    y_array = np.zeros(n, dtype=np.float32)
    z_array = np.zeros(n, dtype=np.float32)
    intensity_array = np.ones(n, dtype=np.float32)
    

    ############################################################################################################################################################################

    holo_gen_1 = HologramGeneratorNumpy()
    holo_gen_1.Initialize_HologramGenerator(width, height, depth, 10, False)
    holo_gen_1.CalculateAffinePolynomials( SLM_X_0=10, SLM_Y_0=10, CAM_X_0=10, CAM_Y_0=10, SLM_X_1=-10, SLM_Y_1=-10, CAM_X_1=-10, CAM_Y_1=-10, SLM_X_2=10, SLM_Y_2=-10, CAM_X_2=10, CAM_Y_2=-10)


    ############################################################################################################################################################################
    print("Generating hologram 2")
    start_time = time.time()

    hologram_image_1 = holo_gen_1.Generate_Hologram(WFC, x_array, y_array, z_array, intensity_array, len(x_array), 1)
    print("Time taken to generate hologram:", time.time() - start_time)

    # normalize to 0-255
    hologram_image_1 = (hologram_image_1 - np.min(hologram_image_1)) / (np.max(hologram_image_1) - np.min(hologram_image_1)) * 255
    hologram_image_1 = hologram_image_1.astype(np.uint8)
    hologram_image_1 = hologram_image_1.reshape([height, width, Bytes])
   

    cv2.imwrite("./imgs/hologram_image_1.png", hologram_image_1)

    # save both the holograms

    
        
    print("Done")

 
       




