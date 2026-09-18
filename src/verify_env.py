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
    "plotly",
    "pulp",
]

FAILED = []

for package in REQUIRED_PACKAGES:
    try:
        module = importlib.import_module(package)
        version = getattr(module, "__version__", "N/A")
        print(f"[OK]   {package:12s} {version}")
    except ImportError as exc:
        print(f"[FAIL] {package:12s} NOT INSTALLED ({exc})")
        FAILED.append(package)

if FAILED:
    print(f"\nMissing packages: {', '.join(FAILED)}. Run: pip install -r requirements.txt")
    raise SystemExit(1)

print("\nAll required libraries installed successfully.")