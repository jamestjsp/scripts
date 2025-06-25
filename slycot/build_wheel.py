# build_wheel.py
import os
import subprocess
import sys
import shutil
import glob
import platform

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

def setup_build_env():
    """Prepare a dictionary with all necessary environment variables for the build."""
    build_env = os.environ.copy()
    vcpkg_root = os.environ.get("VCPKG_ROOT", "C:\\vcpkg")
    build_env["VCPKG_ROOT"] = vcpkg_root
    build_env["CMAKE_TOOLCHAIN_FILE"] = os.path.join(vcpkg_root, "scripts", "buildsystems", "vcpkg.cmake")
    build_env["CMAKE_GENERATOR"] = "MinGW Makefiles"
    build_env["FC"] = "gfortran"
    build_env["CC"] = "gcc"
    build_env["CXX"] = "g++"
    # Add vcpkg DLLs to the PATH so delvewheel can find them
    vcpkg_dll_path = os.path.join(vcpkg_root, "installed", "x64-windows", "bin")
    build_env["PATH"] = f"{vcpkg_dll_path};{build_env['PATH']}"
    return build_env

def main():
    """Main function to build and repair the wheel."""
    check_prerequisites()
    build_env = setup_build_env()

    print("\n===== Installing Build Tools =====")
    try:
        # Install the tools needed for the script itself to run using uv
        subprocess.run(
            ["uv", "pip", "install", "numpy<2.0", "scikit-build", "wheel", "delvewheel"],
            check=True, capture_output=True
        )
        print("✅ Build tools installed successfully.")
    except subprocess.CalledProcessError as e:
        print("❌ ERROR: Failed to install build dependencies.")
        print(e.stderr.decode())
        sys.exit(1)

    try:
        # Step 1: Force a build from source by installing with --no-binary
        print("\n===== Step 1 of 3: Building Slycot from Source =====")
        install_cmd = [
            "uv", "pip", "install",
            "--no-binary=slycot",      # Force slycot to build from source
            "--force-reinstall",    # Ensure a clean build
            "--no-deps",            # We only want to build slycot itself
            "slycot"
        ]
        subprocess.run(install_cmd, check=True, env=build_env)
        print("✅ Slycot built from source successfully.")

        # Step 2: Package the now-installed slycot into a wheel
        print("\n===== Step 2 of 3: Packaging into a Wheel File =====")
        os.makedirs("wheels", exist_ok=True)
        wheel_cmd = [
            "uv", "run", "--with", "pip", "pip", "wheel",
            "--wheel-dir=wheels",
            "--no-deps",  # Package only slycot, not its dependencies
            "slycot"
        ]
        subprocess.run(wheel_cmd, check=True, env=build_env)
        wheel_path = glob.glob("wheels/slycot-*.whl")[0]
        print(f"✅ Wheel created: {wheel_path}")

        # Step 3: Repair the wheel to bundle DLLs
        print("\n===== Step 3 of 3: Repairing Wheel with Delvewheel =====")
        repair_cmd = [
            "uv", "run", "delvewheel", "repair", wheel_path
        ]
        subprocess.run(repair_cmd, check=True, env=build_env)
        print("✅ Wheel repaired successfully.")

    except (subprocess.CalledProcessError, IndexError) as e:
        print("\n❌ ERROR: The build or repair process failed.")
        if hasattr(e, 'stdout') and e.stdout: print(e.stdout.decode())
        if hasattr(e, 'stderr') and e.stderr: print(e.stderr.decode())
        sys.exit(1)

    finally:
        # Clean up the intermediate directory, but leave the final 'wheelhouse'
        if os.path.isdir("wheels"):
            print("\nCleaning up intermediate 'wheels' directory...")
            shutil.rmtree("wheels")

    print("\n" + "="*50)
    print("✅ Success! Build process complete.")
    print("   The final, distributable wheel is in the 'wheelhouse' directory.")
    print("="*50)

if __name__ == "__main__":
    main()
