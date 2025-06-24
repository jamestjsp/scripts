import os
import subprocess
import glob
import shutil
import sys

def main():
    # Set environment variables for MinGW and vcpkg
    os.environ["FC"] = "gfortran"
    os.environ["CC"] = "gcc"
    os.environ["CXX"] = "g++"
    os.environ["CMAKE_GENERATOR"] = "MinGW Makefiles"
    if "VCPKG_ROOT" not in os.environ:
        os.environ["VCPKG_ROOT"] = "C:\\vcpkg"
    os.environ["CMAKE_TOOLCHAIN_FILE"] = os.path.join(os.environ["VCPKG_ROOT"], "scripts", "buildsystems", "vcpkg.cmake")
    
    # Ensure MinGW and vcpkg binaries are on the PATH for delvewheel
    mingw_bin = os.path.dirname(shutil.which("gcc"))
    vcpkg_bin = os.path.join(os.environ["VCPKG_ROOT"], "installed", "x64-windows", "bin")
    if mingw_bin not in os.environ["PATH"]:
         os.environ["PATH"] = f"{mingw_bin};{os.environ['PATH']}"
    if vcpkg_bin not in os.environ["PATH"]:
        os.environ["PATH"] = f"{vcpkg_bin};{os.environ['PATH']}"

    # Install required packages
    print("\n===== Installing Required Packages =====")
    required_packages = [
        "numpy<2.0", "scipy", "scikit-build", "pytest", "wheel", "delvewheel"
    ]
    subprocess.run([sys.executable, "-m", "pip", "install"] + required_packages, check=True)

    # Build, Repair, and Install
    try:
        print("\n===== Building Slycot wheel =====")
        wheel_cmd = [
            "pip", "wheel", ".", "--wheel-dir=wheels",
            "--config-settings=cmake.define.CMAKE_Fortran_FLAGS=-ff2c -fdefault-integer-8 -fdefault-real-8"
        ]
        subprocess.run(wheel_cmd, check=True)
        
        wheel_path = glob.glob("wheels/slycot-*.whl")[0]
        
        print(f"\n===== Repairing wheel '{wheel_path}' with delvewheel =====")
        subprocess.run(["delvewheel", "repair", wheel_path], check=True)
        
        repaired_wheel_path = glob.glob("wheelhouse/slycot-*.whl")[0]
        
        print(f"\n===== Installing repaired wheel '{repaired_wheel_path}' =====")
        subprocess.run(["pip", "install", repaired_wheel_path], check=True)
        
        test_slycot()
        
    except (subprocess.CalledProcessError, IndexError) as e:
        print(f"\n❌ Error during build/repair/install process: {e}")
        sys.exit(1)
    finally:
        # Clean up
        print("\n===== Cleaning Up =====")
        for d in ["wheels", "wheelhouse"]:
            if os.path.isdir(d):
                print(f"Removing temporary '{d}' directory...")
                shutil.rmtree(d)

def test_slycot():
    """Test Slycot installation by running its test suite."""
    print("\n===== Testing Slycot Installation =====")
    try:
        test_cmd = [sys.executable, "-c", "import slycot; slycot.test()"]
        subprocess.run(test_cmd, check=True)
        print("\n✅ Slycot tests PASSED - Installation successful!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Slycot tests FAILED: {e}")

if __name__ == "__main__":
    main()
