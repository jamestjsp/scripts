import os
import subprocess
import shutil
import sys
import platform
import glob

def check_prerequisites():
    """Verify that required tools (uv, gfortran, vcpkg) are available."""
    print("===== Checking Prerequisites =====")
    
    if platform.system() != "Windows":
        print("❌ This script is designed for Windows.")
        sys.exit(1)

    # Check for uv
    if not shutil.which("uv"):
        print("❌ 'uv' is not installed or not in your system's PATH.")
        print("   Please install it from https://github.com/astral-sh/uv")
        sys.exit(1)
    print("✅ Found uv.")

    # Check for gfortran and gcc (MinGW)
    if not shutil.which("gfortran") or not shutil.which("gcc"):
        print("❌ 'gfortran' or 'gcc' not found.")
        print("   Please install a MinGW-w64 toolchain and add its 'bin' directory to your PATH.")
        sys.exit(1)
    print("✅ Found MinGW toolchain (gfortran, gcc).")

    # Check for vcpkg and required DLLs for delvewheel
    vcpkg_root = os.environ.get("VCPKG_ROOT", "C:\\vcpkg")
    blas_lapack_bin = os.path.join(vcpkg_root, "installed", "x64-windows", "bin")
    if not os.path.exists(os.path.join(blas_lapack_bin, "openblas.dll")):
        print(f"❌ Could not find 'openblas.dll' in {blas_lapack_bin}")
        print("   Please ensure vcpkg is installed, openblas/lapack are installed,")
        print("   and the VCPKG_ROOT environment variable is set correctly.")
        print(f"   Also, ensure '{blas_lapack_bin}' is in your PATH for delvewheel to find it.")
        sys.exit(1)
    print("✅ Found vcpkg dependencies.")

    print("All prerequisites are met.\n")

def setup_virtual_env():
    """Create a uv virtual environment if it doesn't exist."""
    print("===== Setting Up Virtual Environment =====")
    if not os.path.exists(".venv"):
        print("Creating virtual environment with 'uv venv'...")
        subprocess.run(["uv", "venv"], check=True, capture_output=True)
        print("✅ Virtual environment created successfully.")
    else:
        print("✅ Virtual environment '.venv' already exists.")
    print(f"Virtual environment Python: {os.path.join(os.getcwd(), '.venv', 'Scripts', 'python.exe')}\n")

def install_dependencies():
    """Install required build and runtime packages using uv."""
    print("===== Installing Build and Runtime Dependencies =====")
    required_packages = [
        "numpy<2.0",
        "scipy",
        "scikit-build",
        "wheel",
        "pytest",
        "build",  # Add build package for creating wheels
        "delvewheel"
    ]
    try:
        print(f"Installing: {', '.join(required_packages)}")
        subprocess.run(["uv", "pip", "install"] + required_packages, check=True, capture_output=True)
        print("✅ All required packages installed successfully.\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install required packages: {e.stderr.decode()}")
        sys.exit(1)

def build_and_repair_wheel():
    """Builds the slycot wheel and repairs it with delvewheel."""
    print("===== Building and Repairing Slycot Wheel =====")
    
    # Set environment variables for MinGW toolchain
    build_env = os.environ.copy()
    build_env["CMAKE_GENERATOR"] = "MinGW Makefiles"
    build_env["FC"] = "gfortran"
    build_env["CC"] = "gcc"
    build_env["CXX"] = "g++"
    
    try:
        # 1. Install slycot from source to trigger build, then create wheel
        print("Installing Slycot from source to build...")
        
        # First install slycot from source (this will build it)
        install_cmd = [
            "uv", "pip", "install", 
            "--no-binary=slycot", 
            "--force-reinstall",
            "slycot"
        ]
        subprocess.run(install_cmd, check=True, env=build_env)
        print("✅ Slycot built and installed from source.")
        
        # 2. Create wheel directory and use pip through uv run --with
        print("Creating wheel from installed package...")
        os.makedirs("wheels", exist_ok=True)
        
        # Use pip through uv run --with to create wheel
        wheel_cmd = [
            "uv", "run", "--with", "pip", "pip", "wheel",
            "--wheel-dir=wheels",
            "--no-deps",
            "slycot"
        ]
        subprocess.run(wheel_cmd, check=True, env=build_env)
        print("✅ Slycot wheel created successfully.")
        
        # Find the built wheel
        wheel_path = glob.glob("wheels/slycot-*.whl")[0]
        
        # 3. Repair the wheel with delvewheel
        print(f"\nRepairing wheel '{wheel_path}' with delvewheel...")
        # Add vcpkg libs to PATH for delvewheel if not already there
        vcpkg_bin_path = os.path.join(os.environ.get("VCPKG_ROOT", "C:\\vcpkg"), "installed", "x64-windows", "bin")
        repair_env = build_env.copy()
        repair_env["PATH"] = f"{vcpkg_bin_path};{repair_env['PATH']}"
        
        repair_cmd = ["uv", "run", "delvewheel", "repair", wheel_path]
        subprocess.run(repair_cmd, check=True, env=repair_env)
        print("✅ Wheel repaired successfully. Final wheel is in 'wheelhouse' directory.")
        
        # 4. Install the repaired wheel
        repaired_wheel_path = glob.glob("wheelhouse/slycot-*.whl")[0]
        print(f"\nInstalling repaired wheel: {repaired_wheel_path}...")
        install_cmd = ["uv", "pip", "install", "--force-reinstall", repaired_wheel_path]
        subprocess.run(install_cmd, check=True)
        print("✅ Slycot installed successfully from repaired wheel.\n")
        
        return True

    except (subprocess.CalledProcessError, IndexError) as e:
        print(f"\n❌ Error during slycot build/repair/install process.")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"   STDERR:\n{e.stderr.decode()}")
        elif hasattr(e, 'stdout') and e.stdout:
             print(f"   STDOUT:\n{e.stdout.decode()}")
        else:
            print(e)
        print("Build failed. Check compiler and library paths.")
        return False

def test_slycot():
    """Test Slycot installation by running its test suite."""
    print("===== Testing Slycot Installation =====")
    print("Running: import slycot; slycot.test()")
    
    try:
        cmd = ["uv", "run", "python", "-c", "import slycot; slycot.test()"]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("\n--- Test Output ---")
        print(result.stdout)
        if result.stderr:
            print("\n--- Test Errors/Warnings ---")
            print(result.stderr)
        print("\n✅ Slycot tests PASSED! Installation is successful and working.")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Slycot tests FAILED.")
        print(f"   STDOUT:\n{e.stdout}")
        print(f"   STDERR:\n{e.stderr}")
    
    print("===== Test Complete =====")

def main():
    """Main function to orchestrate the installation process."""
    try:
        check_prerequisites()
        setup_virtual_env()
        install_dependencies()
        if build_and_repair_wheel():
            test_slycot()
    finally:
        # Clean up temporary directories
        print("\n===== Cleaning Up =====")
        for d in ["wheels", "wheelhouse"]:
            if os.path.isdir(d):
                print(f"Removing temporary '{d}' directory...")
                shutil.rmtree(d)
        print("✅ Cleanup complete.")

if __name__ == "__main__":
    main()
