#!/bin/sh
# Linux: copy the distro nmap + its shared libs into vendor/nmap/ (relocatable via RPATH patch with patchelf)
# Needs: nmap installed (apt/dnf), patchelf
set -e
cd "$(dirname "$0")/.."
BIN=$(command -v nmap) || { echo "install nmap first (apt install nmap patchelf)"; exit 1; }
DATA=$(dirname "$(nmap --version | grep -o '/[^ ]*nmap-services' || echo /usr/share/nmap/nmap-services)")
[ -d "$DATA" ] || DATA=/usr/share/nmap
rm -rf vendor/nmap && mkdir -p vendor/nmap/bin vendor/nmap/lib vendor/nmap/share
cp "$BIN" vendor/nmap/bin/nmap && cp -R "$DATA" vendor/nmap/share/nmap
ldd "$BIN" | awk '/=> \//{print $3}' | grep -vE 'libc\.so|libm\.so|libpthread|libdl|ld-linux|libgcc_s|libstdc\+\+' | while read -r l; do cp -L "$l" vendor/nmap/lib/; done
patchelf --set-rpath '$ORIGIN/../lib' vendor/nmap/bin/nmap
cp /usr/share/doc/nmap/copyright vendor/nmap/LICENSE-nmap.txt 2>/dev/null || true
echo "bundled $(vendor/nmap/bin/nmap --version | head -1) -> vendor/nmap"
