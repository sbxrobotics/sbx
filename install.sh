#!/bin/bash

# ----------------------------------------------------
# Usage: Install the SBX Robotics CLI locally via pip
# Author: SBX Robotics Inc.
# ----------------------------------------------------

cd "$(dirname "$0")"

# use pip to install the cli from the current directory (via setup.py)
pip install -e . --upgrade --force-reinstall