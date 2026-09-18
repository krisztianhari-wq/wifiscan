#!/bin/sh
# Single-file, cross-platform archive: dist/wifiscan.pyz  (needs Python 3.9+ and a system nmap for service detection)
#   ./dist/wifiscan.pyz           -> GUI
#   ./dist/wifiscan.pyz scan      -> terminal
set -e
cd "$(dirname "$0")"
rm -rf build/pyz dist/wifiscan.pyz && mkdir -p build/pyz dist
cp -R wifiscan build/pyz/wifiscan
find build/pyz -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
printf 'import sys\nfrom wifiscan.cli import main\nsys.exit(main())\n' > build/pyz/__main__.py
python3 -m zipapp build/pyz -p "/usr/bin/env python3" -c -o dist/wifiscan.pyz
echo "built dist/wifiscan.pyz ($(wc -c < dist/wifiscan.pyz) bytes)"
