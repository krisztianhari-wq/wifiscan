#!/bin/sh
# Windows (Git Bash / MSYS): fetch nmap from nmap.org into vendor/nmap/
#   1) latest nmap-<ver>-setup.exe extracted with 7-Zip (NSIS archive)  – newest version
#   2) fallback: nmap-7.92-win32.zip (last official portable zip)
# Layout expected by the app: vendor/nmap/bin/nmap.exe (+ dlls) and vendor/nmap/share/nmap/<data files>
# Npcap (raw sockets, -O) must still be installed by the user: https://npcap.com
set -e
cd "$(dirname "$0")/.."
rm -rf vendor/nmap build/nmap-win && mkdir -p vendor/nmap/bin vendor/nmap/share/nmap build/nmap-win
VER=${NMAP_VERSION:-$(curl -fsSL https://nmap.org/dist/ | grep -oE 'nmap-7\.[0-9]+-setup\.exe' | sort -uV | tail -1 | sed -E 's/nmap-(.*)-setup\.exe/\1/')}
SRC=""
if command -v 7z >/dev/null 2>&1 && [ -n "$VER" ]; then
  echo "downloading nmap-$VER-setup.exe"
  curl -fL "https://nmap.org/dist/nmap-$VER-setup.exe" -o build/nmap-win/setup.exe
  7z x -y -obuild/nmap-win/setup build/nmap-win/setup.exe >/dev/null && SRC=build/nmap-win/setup
fi
if [ -z "$SRC" ] || [ ! -f "$SRC/nmap.exe" ]; then
  VER=7.92; echo "falling back to nmap-$VER-win32.zip"
  curl -fL "https://nmap.org/dist/nmap-$VER-win32.zip" -o build/nmap-win/nmap.zip
  (cd build/nmap-win && unzip -q nmap.zip) && SRC=$(ls -d build/nmap-win/nmap-*/ | head -1)
fi
cp "$SRC"/nmap.exe "$SRC"/*.dll vendor/nmap/bin/
for f in nmap-mac-prefixes nmap-os-db nmap-protocols nmap-rpc nmap-service-probes nmap-services nmap.dtd nmap.xsl nse_main.lua; do cp "$SRC/$f" vendor/nmap/share/nmap/ 2>/dev/null || true; done
cp -R "$SRC"/nselib "$SRC"/scripts vendor/nmap/share/nmap/ 2>/dev/null || true
cp "$SRC"/LICENSE vendor/nmap/LICENSE-nmap.txt 2>/dev/null || cp "$SRC"/COPYING vendor/nmap/LICENSE-nmap.txt 2>/dev/null || true
echo "bundled nmap $VER (windows) -> vendor/nmap ($(du -sh vendor/nmap | cut -f1))"
