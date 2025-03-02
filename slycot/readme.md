# 🚀 Installing Slycot on Windows

This guide walks through setting up Slycot in a Windows environment using MinGW, VCPKG, and a Python virtual environment.

## 📋 Prerequisites

### CMake
1. 📥 Download and install CMake from [cmake.org](https://cmake.org/download/)
2. ✅ During installation, select the option to add CMake to your system PATH

### MinGW
1. 📥 **Download MinGW** from GitHub:
   - Go to [MinGW Builds Binaries](https://github.com/niXman/mingw-builds-binaries/releases)
   - Download the latest `x86_64-*-release-posix-seh-ucrt-rt*.7z` file 
   - Example: `x86_64-13.2.0-release-posix-seh-ucrt-rt_v11-rev0.7z`

2. 📂 **Install MinGW:**
   - Extract the downloaded 7z file to `C:\mingw64`
   - You can use [7-Zip](https://www.7-zip.org/) to extract the archive

3. 🌐 **Add to PATH:**
   - Add `C:\mingw64\bin` to your system PATH
   - Open Command Prompt as administrator and run:
     ```bash
     setx /M PATH "%PATH%;C:\mingw64\bin"
     ```

4. ✅ **Verify Installation:**
   - Open a new Command Prompt and check if gcc and gfortran are available:
     ```bash
     gcc --version
     gfortran --version
     ```

### VCPKG
1. 📥 Clone VCPKG repository:
   ```bash
   git clone https://github.com/microsoft/vcpkg.git C:\vcpkg
   ```

2. 🔧 Bootstrap VCPKG:
   ```bash
   cd C:\vcpkg
   .\bootstrap-vcpkg.bat
   ```

3. 📚 Install LAPACK and BLAS:
   ```bash
   .\vcpkg.exe install lapack:x64-windows openblas:x64-windows
   ```

4. 🌐 Set environment variables:
   ```bash
   setx VCPKG_ROOT "C:\vcpkg"
   setx CMAKE_TOOLCHAIN_FILE "C:\vcpkg\scripts\buildsystems\vcpkg.cmake"
   ```

### Python
1. 📥 Download and install Python with development features from [python.org](https://www.python.org/downloads/)
2. ✅ Ensure you check "Download debug binaries" and "Add Python to PATH" during installation

## 🏗️ Setting Up the Environment

### Create a Virtual Environment
1. 📂 Create a directory for your environment:
   ```bash
   mkdir -p C:\devtools\envs
   cd C:\devtools\envs
   ```

2. 🐍 Create a new virtual environment:
   ```bash
   python -m venv <env name>
   ```

3. ⚡ Activate the environment:
   ```bash
   C:\devtools\envs\<env name>\Scripts\activate
   ```

### Install Required Python Packages
```bash
pip install numpy scipy scikit-build pytest wheel setuptools setuptools_scm
```

## 🧪 Installing Slycot

### Method 1: Using the install_slycot.py Script
1. 📋 Save the `install_slycot.py` script to a convenient location (e.g., scripts)

2. 📥 Run the installation script:
   ```bash
   python C:\devtools\scripts\install_slycot.py
   ```

### Method 2: Manual Installation
1. 🔧 Set the necessary environment variables:
   ```bash
   set FC=gfortran
   set CC=gcc
   set CXX=g++
   set CMAKE_GENERATOR=MinGW Makefiles
   ```

2. 🔄 Create a local wheel:
   ```bash
   pip wheel --no-cache-dir --verbose slycot --no-build-isolation --wheel-dir=wheels ^
       --config-settings=cmake.generator="MinGW Makefiles" ^
       --config-settings=cmake.define.CMAKE_C_COMPILER=gcc ^
       --config-settings=cmake.define.CMAKE_CXX_COMPILER=g++ ^
       --config-settings=cmake.define.CMAKE_Fortran_COMPILER=gfortran ^
       --config-settings=cmake.define.CMAKE_Fortran_FLAGS="-ff2c -fdefault-integer-8 -fdefault-real-8 -fPIC"
   ```

3. 📦 Install from the wheel:
   ```bash
   pip install --no-index --find-links=wheels slycot
   ```

4. 📁 Copy the required DLLs to the Slycot installation directory:
   - `libgcc_s_seh-1.dll` (from MinGW bin directory)
   - `libgfortran-5.dll` (from MinGW bin directory)
   - `libquadmath-0.dll` (from MinGW bin directory)
   - `libwinpthread-1.dll` (from MinGW bin directory)
   - `liblapack.dll` (from VCPKG)
   - `openblas.dll` (from VCPKG)

## ✅ Verify the Installation

Run the following to test if Slycot is working correctly:

```python
python -c "import slycot; slycot.test()"
```

## 🔍 Troubleshooting

### Missing DLLs
If you get "DLL not found" errors:
1. Make sure all required DLLs are in the Slycot directory
2. Check Windows environment variables (PATH)
3. Run `install_slycot.py` again with administrator privileges

### Build Failures
If building fails:
1. Ensure MinGW tools (gcc, g++, gfortran) are in your PATH
2. Check that VCPKG has successfully installed LAPACK/BLAS
3. Verify CMake is properly configured for MinGW

### Import Errors
If `import slycot` fails:
1. Ensure NumPy and SciPy are installed
2. Check if required DLLs are accessible
3. Try reinstalling with `pip install --force-reinstall slycot`

## 📝 Notes

- Slycot requires LAPACK and BLAS libraries for numerical computations
- The MinGW compiler is used instead of MSVC because of Fortran requirements
- Slycot needs Python 3.10+
