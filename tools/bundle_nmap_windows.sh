#!/bin/sh
# Windows (Git Bash / MSYS): download the official portable nmap zip from nmap.org into vendor/nmap/
# Layout expected by the app: vendor/nmap/bin/nmap.exe + vendor/nmap/share/nmap/<data files>
# Npcap (raw sockets, -O) must still be installed separately by the user: https://npcap.com
set -e
cd "$(dirname "$0")/.."
VER=${NMAP_VERSION:-7.98}
URL="https://nmap.org/dist/nmap-$VER-win32.zip"
rm -rf vendor/nmap build/nmap-win && mkdir -p vendor/nmap/bin vendor/nmap/share build/nmap-win
curl -fL "$URL" -o build/nmap-win/nmap.zip
(cd build/nmap-win && unzip -q nmap.zip)
SRC=$(ls -d build/nmap-win/nmap-*/ | head -1)
cp "$SRC"/*.exe "$SRC"/*.dll vendor/nmap/bin/ 2>/dev/null || true
mkdir -p vendor/nmap/share/nmap && cp -R "$SRC"/nmap-* "$SRC"/nse_main.lua "$SRC"/nselib "$SRC"/scripts "$SRC"/nmap.dtd "$SRC"/nmap.xsl vendor/nmap/share/nmap/ 2>/dev/null || true
cp "$SRC"/LICENSE vendor/nmap/LICENSE-nmap.txt 2>/dev/null || true
echo "bundled nmap $VER (win32) -> vendor/nmap"
