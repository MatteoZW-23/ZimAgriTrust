import numpy as np

def prove_backpropagation():
    """
    Sovereign Proof: Backpropagation and Weight Optimization.
    This script proves how a Neural Network "learns" by calculating 
    gradients and updating weights to minimize error.
    """
    print("==================================================")
    print("DEEP LEARNING PROOF: BACKPROPAGATION CORE")
    print("==================================================")

    # 1. SIMPLE NEURAL UNIT (Perceptron)
    # Weights and Bias
    w = 0.5
    b = 0.1
    x = 2.0  # Input
    y_target = 5.0 # We want the network to output 5.0
    
    lr = 0.1 # Learning Rate
    
    print(f"[INITIAL STATE] Input: {x}, Weight: {w}, Bias: {b}, Target: {y_target}")

    # 2. THE LEARNING LOOP
    print("\n[TRAINING PROGRESS]")
    for epoch in range(1, 41):
        # FORWARD PASS
        y_pred = w * x + b
        
        # CALCULATE LOSS (MSE)
        loss = (y_pred - y_target)**2
        
        # BACKWARD PASS (The "Chain Rule" Proof)
        # dL/dy_pred = 2 * (y_pred - y_target)
        # dy_pred/dw = x
        # dy_pred/db = 1
        
        grad_w = 2 * (y_pred - y_target) * x
        grad_b = 2 * (y_pred - y_target) * 1
        
        # WEIGHT UPDATE (The "Optimization" Proof)
        w = w - lr * grad_w
        b = b - lr * grad_b
        
        if epoch % 5 == 0 or epoch == 1:
            print(f"Epoch {epoch:2d}: Pred={y_pred:6.4f}, Loss={loss:6.4f}, Weight={w:6.4f}")

    # 3. VERIFICATION
    final_pred = w * x + b
    print(f"\n[FINAL STATE] Optimized Prediction: {final_pred:6.4f}")
    print(f"Convergence Error: {abs(final_pred - y_target):.6f}")

    if abs(final_pred - y_target) < 0.01:
        print("\nVerdict: Gradient Descent has Successfully Converged.")
        print("Proof: Neural weights adapted to capture the target market dynamic.")
    else:
        print("\nVerdict: Convergence unstable. Parameters require refinement.")

    print("\n==================================================")
    print("DEEP LEARNING CONCEPT PROVEN.")
    print("==================================================")

if __name__ == "__main__":
    prove_backpropagation()
