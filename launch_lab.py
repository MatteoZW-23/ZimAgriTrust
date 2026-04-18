import subprocess
import sys
import os

def check_and_install_jupyter():
    """
    Configures and initializes the Sovereign AI Research Lab.
    Isolates Jupyter dependencies and ensures the kernel is ready.
    """
    print("==================================================")
    print("AGRITRUST: AI RESEARCH LAB CONFIGURATOR")
    print("==================================================")

    # 1. DEFINE REQUIREMENTS
    ds_requirements = [
        "jupyter",
        "notebook",
        "ipykernel",
        "matplotlib",
        "seaborn",
        "pandas",
        "numpy",
        "scikit-learn",
        "tensorflow"
    ]

    print("\n[STEP 1] Auditing Scientific Environment...")
    try:
        import jupyter
        print("Success: Jupyter core identified.")
    except ImportError:
        print("Action: Jupyter missing. Installing Scientific Suite...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *ds_requirements])

    # 2. CONFIGURE KERNEL
    print("\n[STEP 2] Configuring AgriTrust Research Kernel...")
    subprocess.check_call([
        sys.executable, "-m", "ipykernel", "install", 
        "--user", "--name", "agritrust_env", 
        "--display-name", "AgriTrust AI Core (Scientific)"
    ])

    # 3. LAUNCH LAB
    print("\n[STEP 3] Initializing Sovereign AI Laboratory...")
    print("Target: research/labs/agritrust_ai_lab.ipynb")
    print("-" * 50)
    
    # We use subprocess.Popen to let it run in the background
    lab_path = os.path.join("research", "labs", "agritrust_ai_lab.ipynb")
    
    try:
        # Launching with specific browser-less flag first just to check, 
        # but usually we want it to open a browser for the user.
        subprocess.run([sys.executable, "-m", "notebook", lab_path], check=True)
    except KeyboardInterrupt:
        print("\nLab session terminated by user.")
    except Exception as e:
        print(f"Error launching lab: {e}")

if __name__ == "__main__":
    # Check if we are in the root
    if not os.path.exists("research/labs"):
        print("Error: Please run this script from the project root.")
    else:
        check_and_install_jupyter()
