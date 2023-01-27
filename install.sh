#!/bin/bash
# Usage: Installs the SBX Robotics CLI package
# Author: SBX Robotics Inc.
# -------------------------------------------------

cd "$(dirname "$0")"

#python3 setup.py clean --all install --user --force
pip install -e . --upgrade --force-reinstall