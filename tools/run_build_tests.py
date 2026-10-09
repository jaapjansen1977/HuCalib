"""Keep native stderr out of PowerShell's error pipeline; retain full test logs."""
import argparse
from pathlib import Path
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--log', type=Path, required=True)
args = parser.parse_args()
with args.log.open('w', encoding='utf-8') as log:
    result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                            stdout=log, stderr=subprocess.STDOUT)
print(f'Unit-tests exitcode {result.returncode}; log: {args.log}')
raise SystemExit(result.returncode)
