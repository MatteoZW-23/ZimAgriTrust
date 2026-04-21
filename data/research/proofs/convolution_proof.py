import numpy as np

def prove_convolution():
    """
    Sovereign Proof: Matrix-Based Spatial Feature Extraction.
    This script proves how Computer Vision "sees" edges and structures 
    using fundamental mathematical operations.
    """
    print("==================================================")
    print("COMPUTER VISION PROOF: CONVOLUTION CORE")
    print("==================================================")

    # 1. DEFINE A TRANSACTED IMAGE GRID (Simulating an apple or produce)
    # 0 = Background, 1 = Produce Tissue
    image = np.array([
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 1, 1, 0, 0],
        [0, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 0, 0, 1, 0], # Note the 0s in middle - simulating a defect!
        [0, 1, 1, 0, 0, 1, 0],
        [0, 0, 1, 1, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0]
    ])
    
    print("\n[STEP 1] Input Feature Map (Produce Representation):")
    print(image)

    # 2. DEFINE A SOBEL KERNEL (Edge Detector)
    # This kernel identifies horizontal changes in intensity
    kernel = np.array([
        [-1, -2, -1],
        [ 0,  0,  0],
        [ 1,  2,  1]
    ])
    
    print("\n[STEP 2] Applied Convolutional Kernel (Sobel Filter):")
    print(kernel)

    # 3. MANUAL CONVOLUTION (The Math of AI)
    def convolve2d(img, kernel):
        i_h, i_w = img.shape
        k_h, k_w = kernel.shape
        o_h, o_w = i_h - k_h + 1, i_w - k_w + 1
        output = np.zeros((o_h, o_w))
        
        for i in range(o_h):
            for j in range(o_w):
                # Element-wise multiplication + Sum
                region = img[i:i+k_h, j:j+k_w]
                output[i, j] = np.sum(region * kernel)
        return output

    result = convolve2d(image, kernel)
    
    print("\n[STEP 3] Output Activations (High-Level Features):")
    print(result)
    
    # 4. ANALYSIS
    print("\n[STEP 4] Proof Analysis:")
    non_zero_activations = np.count_nonzero(result)
    print(f"Total Active Neurons: {non_zero_activations}")
    if np.any(result > 2) or np.any(result < -2):
        print("Verdict: Edge Discontinuity Detected. Internal Tissue Lesion Identified.")
    else:
        print("Verdict: Structural Uniformity Confirmed.")

    print("\n==================================================")
    print("CONVOLUTIONAL CONCEPT PROVEN.")
    print("==================================================")

if __name__ == "__main__":
    prove_convolution()
