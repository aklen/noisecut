#!/usr/bin/env python3
"""
noisecut
--------
Cut through compiler noise. See what really matters.
A build output analyzer for C/C++ projects that transforms raw compiler output
into clear, actionable insight.

Original author: Akos Hamori
Website: https://akoshamori.com/

This is a backward-compatible wrapper around the new modular noisecut package.
For the new modular implementation, use: python -m noisecut
"""

import sys

# Import from the new modular structure
from noisecut.cli import main

if __name__ == '__main__':
    sys.exit(main())
