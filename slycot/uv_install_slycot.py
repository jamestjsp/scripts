import os
import subprocess
import shutil
import sys
import platform

def check_prerequisites():
    """Verify that required tools (uv, gfortran) are available on the PATH."""
    print("===== Checking Prerequisites =====")
    
    if platform.system() != "Windows":
        print("❌ This script is designed for Windows with a MinGW toolchain.")
        sys.exit(1)

    uv_path = shutil.which("uv")
    if not uv_path:
        print("❌ 'uv' is not installed or not in your system's PATH.")
        print("   Please install it from https://github.com/astral-sh/uv")
        sys.exit(1)
    print(f"✅ Found uv at: {uv_path}")

    gfortran_path = shutil.which("gfortran")
    if not gfortran_path:
        print("❌ 'gfortran' is not installed or not in your system's PATH.")
        print("   Please install a MinGW-w64 toolchain (e.g., via MSYS2) and add it to your PATH.")
        sys.exit(1)
    print(f"✅ Found gfortran at: {gfortran_path}")
    
    gcc_path = shutil.which("gcc")
    if not gcc_path:
        print("❌ 'gcc' not found. Please ensure your MinGW-w64 toolchain is complete.")
        sys.exit(1)
    print(f"✅ Found gcc at: {gcc_path}")

    print("All prerequisites are met.\n")
    return os.path.dirname(gfortran_path) # Return MinGW bin path for later use

def setup_virtual_env():
    """Create a uv virtual environment if it doesn't exist."""
    print("===== Setting Up Virtual Environment =====")
    if not os.path.exists(".venv"):
        print("Creating virtual environment with 'uv venv'...")
        try:
            # Create venv and specify a python version if needed, e.g., ["uv", "venv", "-p", "3.11"]
            subprocess.run(["uv", "venv"], check=True, capture_output=True)
            print("✅ Virtual environment created successfully.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create virtual environment: {e.stderr.decode()}")
            sys.exit(1)
    else:
        print("✅ Virtual environment '.venv' already exists.")
    
    # Get the full path to the python interpreter in the venv
    python_executable = get_venv_python_path()
    print(f"Virtual environment Python: {python_executable}\n")
    return python_executable

def install_dependencies():
    """Install required build and runtime packages using uv."""
    print("===== Installing Build and Runtime Dependencies =====")
    required_packages = [
        "numpy<2.0",  # Slycot has known issues with NumPy 2.x
        "scipy",
        "scikit-build",
        "wheel",
        "pytest"
    ]
    try:
        print(f"Installing: {', '.join(required_packages)}")
        cmd = ["uv", "pip", "install"] + required_packages
        # We capture output to avoid flooding the console but show it on error
        subprocess.run(cmd, check=True, text=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        print("✅ All required packages installed successfully.\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install required packages.")
        print(f"   STDOUT: {e.stdout}")
        print(f"   STDERR: {e.stderr}")
        sys.exit(1)

def get_venv_python_path():
    """Gets the path to the python executable inside the .venv"""
    if platform.system() == "Windows":
        return os.path.join(os.getcwd(), ".venv", "Scripts", "python.exe")
    else:
        return os.path.join(os.getcwd(), ".venv", "bin", "python")

def run_in_venv(command):
    """Helper to run a python command inside the uv virtual environment."""
    python_executable = get_venv_python_path()
    try:
        # Run the command using the venv's python
        result = subprocess.run([python_executable, "-c", command], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running command in venv: '{command}'")
        print(f"   STDERR: {e.stderr}")
        return None

def install_slycot():
    """Builds and installs the slycot wheel using uv."""
    print("===== Building and Installing Slycot =====")
    
    # Create a directory to store the built wheel
    if not os.path.exists("wheels"):
        os.makedirs("wheels")

    # Set environment variables directly to force the build system to use MinGW.
    # This is more reliable than passing config settings through multiple tool layers.
    build_env = os.environ.copy()
    build_env["CMAKE_GENERATOR"] = "MinGW Makefiles"
    build_env["FC"] = "gfortran"
    build_env["CC"] = "gcc"
    build_env["CXX"] = "g++"
    print("Build environment configured to use MinGW Makefiles and gfortran.")

    # We use `pip wheel` run via `uv` for robust build-system integration.
    cmd = [
        "uv", "run", "pip", "wheel",
        "--wheel-dir=wheels",
        "--no-build-isolation",
        "--verbose",
        "slycot",
    ]
    
    try:
        print("Building Slycot wheel...")
        print(f"Running command: {' '.join(cmd)}")
        # Run with detailed output shown directly to the user, using the modified environment
        subprocess.run(cmd, check=True, env=build_env)
        print("✅ Slycot wheel built successfully.")
        
        print("\nInstalling from the built wheel...")
        # Install from the locally built wheel using uv
        install_cmd = ["uv", "pip", "install", "--no-index", "--find-links=wheels", "slycot"]
        subprocess.run(install_cmd, check=True, capture_output=True, text=True)
        print("✅ Slycot installed successfully from local wheel.\n")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error during slycot build/install process.")
        # For build errors, the output is often verbose and in stdout/stderr
        if hasattr(e, 'stdout') and e.stdout:
            print(f"   STDOUT:\n{e.stdout}")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"   STDERR:\n{e.stderr}")
        print("Build failed. Check compiler and library paths.")
        return False

def copy_required_dlls(mingw_bin_path):
    """Copy required MinGW, BLAS, and LAPACK runtime DLLs to the Slycot package directory."""
    print("===== Copying Required Runtime DLLs =====")
    
    # Use sysconfig.get_path('purelib') for a more reliable way to find site-packages
    site_packages = run_in_venv("import sysconfig; print(sysconfig.get_path('purelib'))")
    if not site_packages:
        print("❌ Could not determine site-packages directory.")
        return

    slycot_dir = os.path.join(site_packages, "slycot")
    if not os.path.isdir(slycot_dir):
        print(f"❌ Error: Slycot installation directory not found at {slycot_dir}")
        return
    print(f"Slycot installation found at: {slycot_dir}")
    
    # Define source directories for DLLs
    # Assumes OpenBLAS/LAPACK are installed via vcpkg
    vcpkg_root = os.environ.get("VCPKG_ROOT", "C:\\vcpkg")
    blas_lapack_dir = os.path.join(vcpkg_root, "installed", "x64-windows", "bin")
    print(f"Searching for BLAS/LAPACK DLLs in: {blas_lapack_dir}")

    # Dictionary mapping DLLs to their source directory
    required_dll_locations = {
        "libgfortran-5.dll": mingw_bin_path,
        "libgcc_s_seh-1.dll": mingw_bin_path,
        "libquadmath-0.dll": mingw_bin_path,
        "libwinpthread-1.dll": mingw_bin_path,
        "liblapack.dll": blas_lapack_dir,
        "openblas.dll": blas_lapack_dir
    }
    
    for dll, src_dir in required_dll_locations.items():
        src_path = os.path.join(src_dir, dll)
        if os.path.exists(src_path):
            print(f"Copying {dll} from {src_dir}...")
            shutil.copy2(src_path, slycot_dir)
        else:
            print(f"⚠️ Warning: DLL not found and could not be copied: {src_path}")
            print(f"   Your slycot installation may fail at runtime if this DLL is required.")
    
    print("✅ DLL copying process complete.\n")

def test_slycot():
    """Test Slycot installation by running its test suite using uv."""
    print("===== Testing Slycot Installation =====")
    print("Running: import slycot; slycot.test()")
    
    try:
        # Use uv to run the test command in the venv
        cmd = ["uv", "run", "python", "-c", "import slycot; slycot.test()"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            print("❌ Test failed: Slycot could not be imported.")
            print("   This often means a required DLL is missing. Please check the DLL copy step.")
            print(f"   STDERR:\n{result.stderr}")
            return

        print("\n--- Test Output ---")
        print(result.stdout)
        if result.stderr:
            print("\n--- Test Errors/Warnings ---")
            print(result.stderr)
        
        # Pytest returns 0 on success, 1 on test failure, 2 on interruption, etc.
        if result.returncode == 0:
            print("\n✅ Slycot tests PASSED! Installation is successful and working.")
        else:
            print(f"\n❌ Slycot tests FAILED with exit code {result.returncode}. Please review the output.")

    except Exception as e:
        print(f"\n❌ An unexpected error occurred while running Slycot tests: {e}")
    
    print("===== Test Complete =====")

def main():
    """Main function to orchestrate the installation process."""
    mingw_path = check_prerequisites()
    setup_virtual_env()
    install_dependencies()
    if install_slycot():
        copy_required_dlls(mingw_path)
        test_slycot()

if __name__ == "__main__":
    main()
