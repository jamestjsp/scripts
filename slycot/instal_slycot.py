import os
import subprocess
import glob
import tempfile
import shutil
import sys
import site
import importlib.util

def main():
    # Set environment variables for MinGW toolchain
    os.environ["FC"] = "gfortran"
    os.environ["CC"] = "gcc"
    os.environ["CXX"] = "g++"
    os.environ["CMAKE_GENERATOR"] = "MinGW Makefiles"
    
    # Set VCPKG_ROOT and CMAKE_TOOLCHAIN_FILE if they don't exist
    if "VCPKG_ROOT" not in os.environ:
        vcpkg_default = "C:\\vcpkg"
        print(f"VCPKG_ROOT not set, using default: {vcpkg_default}")
        os.environ["VCPKG_ROOT"] = vcpkg_default
    
    if "CMAKE_TOOLCHAIN_FILE" not in os.environ:
        toolchain_path = os.path.join(os.environ["VCPKG_ROOT"], "scripts", "buildsystems", "vcpkg.cmake")
        print(f"CMAKE_TOOLCHAIN_FILE not set, using: {toolchain_path}")
        os.environ["CMAKE_TOOLCHAIN_FILE"] = toolchain_path

    # Clean up previous build attempts
    temp_dir = tempfile.gettempdir()
    slycot_build_dirs = glob.glob(os.path.join(temp_dir, "pip-build-*", "slycot"))
    for build_dir in slycot_build_dirs:
        print(f"Removing {build_dir}")
        shutil.rmtree(build_dir, ignore_errors=True)

    # Install all required packages for building and running Slycot
    print("\n===== Installing Required Packages =====")
    required_packages = [
        "numpy<2.0",  # Use NumPy 1.x which is compatible with Slycot
        "scipy",
        "scikit-build",
        "pytest",
        "wheel",
        "setuptools",
        "setuptools_scm"
    ]
    
    try:
        print(f"Installing packages: {', '.join(required_packages)}")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade"] + required_packages, check=True)
        print("All required packages installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install required packages: {e}")
        return
    
    # Check NumPy version for compatibility
    try:
        import numpy
        numpy_version = numpy.__version__
        print(f"Using NumPy version: {numpy_version}")
        if numpy_version.startswith('2.'):
            print("WARNING: NumPy 2.x detected. Slycot may not be compatible with NumPy 2.x.")
            print("Consider using NumPy 1.x (downgrade to numpy<2.0) for better compatibility.")
            proceed = input("Continue anyway? (y/n): ")
            if proceed.lower() != 'y':
                print("Installation aborted.")
                return
    except ImportError:
        print("Could not verify NumPy version.")
    
    # Get NumPy include directory
    numpy_include_dir = get_numpy_include_dir()
    if not numpy_include_dir:
        print("Failed to locate NumPy include directory!")
        return
    print(f"NumPy include directory: {numpy_include_dir}")

    # Create wheels directory if it doesn't exist
    if not os.path.exists("wheels"):
        os.makedirs("wheels")

    # Build wheel but don't install yet
    cmd = [
        "pip", "wheel", "--no-cache-dir", "--verbose", "slycot",
        "--no-build-isolation",
        "--wheel-dir=wheels",
        "--config-settings=cmake.generator=MinGW Makefiles",
        "--config-settings=cmake.define.CMAKE_C_COMPILER=gcc",
        "--config-settings=cmake.define.CMAKE_CXX_COMPILER=g++",
        "--config-settings=cmake.define.CMAKE_Fortran_COMPILER=gfortran",
        "--config-settings=cmake.define.CMAKE_Fortran_FLAGS=-ff2c -fdefault-integer-8 -fdefault-real-8 -fPIC",
        f"--config-settings=cmake.define.Python_NumPy_INCLUDE_DIR={numpy_include_dir}",
        f"--config-settings=cmake.define.NumPy_INCLUDE_DIR={numpy_include_dir}"
    ]
    
    try:
        print("\n===== Building Slycot wheel =====")
        print(f"Running command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        
        # Install from the saved wheel
        print("\n===== Installing from saved wheel =====")
        subprocess.run(["pip", "install", "--no-index", "--find-links=wheels", "slycot"], check=True)
        
        # Copy required DLLs to Slycot installation location
        copy_required_dlls()
        
        # Test the Slycot installation
        test_slycot()
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error during build/install process: {e}")
        print("You might try running with elevated privileges or checking your environment setup.")
        sys.exit(1)

def get_numpy_include_dir():
    """Get the NumPy include directory"""
    try:
        numpy_spec = importlib.util.find_spec("numpy")
        if numpy_spec and numpy_spec.origin:
            import numpy
            return numpy.get_include()
    except (ImportError, AttributeError) as e:
        print(f"Error finding NumPy: {e}")
    return None

def get_site_packages():
    """Get the correct site-packages directory, considering virtual environments"""
    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("Running in a virtual environment")
        # In a virtual environment, use sys.prefix
        if sys.platform == 'win32':
            return os.path.join(sys.prefix, 'Lib', 'site-packages')
        else:
            return os.path.join(sys.prefix, 'lib', 'python' + sys.version[:3], 'site-packages')
    else:
        # Not in a virtual environment
        print("Not running in a virtual environment")
        return site.getsitepackages()[0]

def copy_required_dlls():
    """Copy required DLLs to the Slycot package installation directory"""
    print("\nCopying required DLLs to Slycot installation directory...")
    
    # Get Python site-packages directory (considering virtual environments)
    site_packages = get_site_packages()
    slycot_dir = os.path.join(site_packages, "slycot")
    
    print(f"Looking for Slycot in: {slycot_dir}")
    if not os.path.exists(slycot_dir):
        print(f"Error: Slycot installation directory not found at {slycot_dir}")
        return
    else:
        print(f"Found Slycot installation at {slycot_dir}")
        
    # MinGW DLLs - adjust paths based on your MinGW installation
    mingw_bin = os.path.dirname(shutil.which("gcc")) or "C:\\mingw64\\bin"
    
    # BLAS and LAPACK DLLs - adjust paths based on your installation
    blas_lapack_dir = os.path.join(os.environ.get("VCPKG_ROOT", "C:\\vcpkg"), 
                                  "installed", "x64-windows", "bin")
    
    # List of DLLs to copy
    required_dlls = {
        "libgcc_s_seh-1.dll": mingw_bin,
        "libgfortran-5.dll": mingw_bin,
        "libquadmath-0.dll": mingw_bin,
        "libwinpthread-1.dll": mingw_bin,
        "liblapack.dll": blas_lapack_dir,
        "openblas.dll": blas_lapack_dir
    }
    
    # Copy DLLs
    for dll, src_dir in required_dlls.items():
        src_path = os.path.join(src_dir, dll)
        if os.path.exists(src_path):
            print(f"Copying {dll}")
            shutil.copy2(src_path, slycot_dir)
        else:
            print(f"Warning: {dll} not found in {src_dir}")
            # Try to find the DLL elsewhere
            alternative_dirs = [
                os.getcwd(),
                os.path.join(os.environ.get("VCPKG_ROOT", "C:\\vcpkg"), "installed", "x64-windows", "bin"),
                os.path.dirname(sys.executable),
                # Add a specific virtual environment directory for fallback
                # "C:\\<Path to your virtaul env>\\Lib\\site-packages\\slycot"
            ]
            
            found = False
            for alt_dir in alternative_dirs:
                alt_path = os.path.join(alt_dir, dll)
                if os.path.exists(alt_path):
                    print(f"Found {dll} in {alt_dir}")
                    shutil.copy2(alt_path, slycot_dir)
                    found = True
                    break
                    
            if not found:
                print(f"Error: Could not find {dll} in any known location")
    
    print("DLL copying completed")

def test_slycot():
    """Test Slycot installation by running its test suite"""
    print("\n===== Testing Slycot Installation =====")
    print("Running: import slycot; slycot.test()")
    
    try:
        # Using subprocess to run in a controlled environment
        test_cmd = [sys.executable, "-c", "import slycot; slycot.test()"]
        result = subprocess.run(test_cmd, capture_output=True, text=True, check=False)
        
        # Print test output
        print("\nTest Output:")
        print(result.stdout)
        
        if result.stderr:
            print("\nTest Errors/Warnings:")
            print(result.stderr)
        
        # Check test result
        if result.returncode == 0:
            print("\n✅ Slycot tests PASSED - Installation successful!")
            
            # Check for warnings in the output
            if "warning" in result.stdout.lower() or "warning" in result.stderr.lower():
                print("\nNote: Some warnings were detected during testing. These are usually harmless,")
                print("but you might want to review them in the test output above.")
            
            # Add installation success information
            print("\nSlycot is now installed and ready to use!")
            print("You can import it in your Python code with: import slycot")
            print("For examples and documentation, visit: https://github.com/python-control/Slycot")
        else:
            print("\n❌ Slycot tests FAILED - There may be issues with the installation.")
            print(f"Exit code: {result.returncode}")
    
    except Exception as e:
        print(f"\n❌ Error running Slycot tests: {e}")
    
    print("===== Test Complete =====")

if __name__ == "__main__":
    main()