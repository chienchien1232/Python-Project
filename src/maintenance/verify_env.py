"""Verify that all required libraries are installed and print their versions."""

import importlib

REQUIRED_PACKAGES = [
    "pandas",
    "numpy",
    "matplotlib",
    "seaborn",
    "streamlit",
    "openpyxl",
    "sklearn",
    # Additive: cac thu vien pipeline ML/UI thuc su import (khong xoa cu).
    "plotly",
    "pulp",
    "pyarrow",
]

def main():
    """Kiem tra import + in version tung thu vien; exit(1) neu thieu."""
    failed = []
    for package in REQUIRED_PACKAGES:
        try:
            module = importlib.import_module(package)
            version = getattr(module, "__version__", "N/A")
            print(f"[OK]   {package:12s} {version}")
        except ImportError as exc:
            print(f"[FAIL] {package:12s} NOT INSTALLED ({exc})")
            failed.append(package)
    if failed:
        print(f"\nMissing packages: {', '.join(failed)}. Run: pip install -r requirements.txt")
        raise SystemExit(1)
    print("\nAll required libraries installed successfully.")


if __name__ == "__main__":
    main()