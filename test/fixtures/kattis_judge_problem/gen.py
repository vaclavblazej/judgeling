#!/usr/bin/env python3
import sys

target_folder = sys.argv[2]
with open(target_folder + "/001.in", "w") as f:
    f.write("3\n5 3 9\n")
