#!/usr/bin/env python3
"""
Launcher for Spam Benchmark with Interactive Model Selection.
"""

import subprocess
import sys
import os
from model_selector import select_model


def main():
    print("🚀 Spam Benchmark Launcher")
    print("==========================")

    model = select_model()

    if not model:
        print("No model selected. Exiting.")
        sys.exit(1)

    print(f"\nSelected model: {model}")
    print("Starting benchmark...\n")

    # Construct the command to run the actual benchmark script
    # We assume spam_benchmark.py is in the same directory
    script_path = os.path.join(os.path.dirname(__file__), "spam_benchmark.py")

    cmd = [sys.executable, script_path, "--model", model]

    # Pass through any additional arguments (like --quick)
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Benchmark failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\n⚠️  Benchmark interrupted.")
        sys.exit(130)


if __name__ == "__main__":
    main()
