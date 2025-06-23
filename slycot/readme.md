# 🚀 Installing Slycot on Windows (The Easy Way)

This guide provides a robust, step-by-step process for installing the `slycot` library on Windows. It uses automated scripts to handle the complex build process involving Fortran, MinGW, and vcpkg.

---

## 📋 Prerequisites

Before running the installation scripts, you must set up the necessary build tools on your system.

### 1. Python
- Download and install a recent version of Python (3.9+) from [python.org](https://www.python.org/).
- **Important:** During installation, ensure you check the box for **"Add python.exe to PATH"**.

### 2. CMake
- Download and install the latest version of [CMake](https://cmake.org/).
- During installation, select:
  - **"Add CMake to the system PATH for all users"** or 
  - **"Add CMake to the system PATH for the current user"**

### 3. MinGW-w64 (Fortran/C/C++ Compiler)
- The build process requires the `gfortran` compiler (not included with Visual Studio).
- **Download:** Go to the [MinGW-w64 builds](https://github.com/brechtsanders/winlibs_mingw/releases) on GitHub.
  - Download a recent version like:
    ```
    x86_64-14.1.0-release-posix-seh-ucrt-rt_v12-rev1.7z
    ```
- **Extract:** Use [7-Zip](https://www.7-zip.org/) to extract to a simple path, e.g., `C:\mingw64`.
- **Add to PATH:** Add `C:\mingw64\bin` to your system’s PATH environment variable.
- **Verify:** Open a new terminal and run:
```sh
  gfortran --version
  gcc --version
```

### 4. Vcpkg (for BLAS and LAPACK libraries)

* **Clone Repo:**

  ```sh
  git clone https://github.com/microsoft/vcpkg.git C:\vcpkg
  ```
* **Bootstrap:**

  ```sh
  cd C:\vcpkg
  .\bootstrap-vcpkg.bat
  ```
* **Install Libraries:**

  ```sh
  .\vcpkg.exe install openblas:x64-windows lapack:x64-windows
  ```
* **Set Environment Variable:**

  ```sh
  setx VCPKG_ROOT "C:\vcpkg"
  ```

  > ℹ️ You may need to restart your terminal for this variable to be recognized.

---

## ⚙️ Automated Installation

After completing the prerequisites, choose one of the following methods:

### Method 1: ✅ Recommended (Using `uv_install_slycot.py`)

This method uses `uv`, a modern and fast Python package installer. It handles:

* Creating a virtual environment
* Building Slycot
* Copying all required DLLs
* Running tests

### ✅ Install `uv` (Recommended)

To install `uv` on Windows, use the official standalone installer via PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

> ℹ️ This script downloads and installs `uv` and `uvx` into a directory such as `$HOME\.local\bin`, and modifies your shell profile to make them available in your terminal.

#### 🔁 Optional: Install a specific version

To install a specific version (e.g., 0.7.13):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/0.7.13/install.ps1 | iex"
```

#### 🛠️ Alternative Installation Methods

If you prefer another package manager:

* **WinGet**:

  ```powershell
  winget install --id=astral-sh.uv -e
  ```

* **Scoop**:

  ```powershell
  scoop install main/uv
  ```

* **PyPI** (requires Rust toolchain if wheel not available):

  ```bash
  pipx install uv  # Recommended if using PyPI
  # or
  pip install uv
  ```

> ⚠️ Installing via `pip` may require a working [Rust](https://www.rust-lang.org/tools/install) toolchain if a prebuilt wheel is not available for your platform.

#### ➤ Run the Script

Navigate to your project directory and run:

```sh
python uv_install_slycot.py
```

> This creates a `.venv` folder, installs everything, and verifies the setup.

---

### Method 2: 🧰 Alternative (Using `install_slycot.py`)

This uses standard `venv` and `pip`. Use this if you prefer not to use `uv`.

#### ➤ Create and Activate a Virtual Environment

```sh
python -m venv .venv
.\.venv\Scripts\activate
```

#### ➤ Run the Script

```sh
python install_slycot.py
```

> This builds and installs `slycot`, copies the necessary DLLs, and runs tests.

---

## ✅ Verification

Both scripts automatically run the `slycot` test suite. If all tests pass, installation is successful.

You can also manually verify:

```sh
# For uv: venv is managed automatically
# For pip: activate the venv first
.\.venv\Scripts\activate
python -c "import slycot; slycot.test()"
```

---

## 🔍 Troubleshooting

| Error                                  | Solution                                                             |
| -------------------------------------- | -------------------------------------------------------------------- |
| `gfortran not found` / `gcc not found` | Ensure `C:\mingw64\bin` is in your PATH. Restart your terminal.      |
| `DLL load failed` / `ImportError`      | Missing DLLs. Ensure vcpkg is correctly set up and rerun the script. |
| Build failures                         | Double-check all prerequisites, especially `vcpkg install` commands. |

---

Happy coding! 🎉
