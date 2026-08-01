"""Entry point for the WMMR ctypes test suite.

Usage:
    python32\\python.exe run_tests.py <path-to-build_clean-bin-Debug>
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import test_wmmr

if __name__ == "__main__":
    sys.exit(test_wmmr.main(sys.argv[1:]))
