"""
Compatibility entry point for `python -m test_gap_analyzer.analyze`.
"""
import sys

from .analyzer import main


if __name__ == "__main__":
    sys.exit(main())
