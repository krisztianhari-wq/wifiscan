#!/bin/sh
# Linux: copy the distro nmap + its shared libs into vendor/nmap/ (relocatable: RPATH=$ORIGIN/../lib via patchelf)
# Needs: nmap and patchelf installed (apt install nmap patchelf)
set -e
cd "$(dirname "$0")/.."
BIN=$(command -v nmap) || { echo "install nmap first (apt install nmap patchelf)"; exit 1; }
DATA=/usr/share/nmap; [ -d "$DATA" ] || DATA=/usr/local/share/nmap
rm -rf vendor/nmap && mkdir -p vendor/nmap/bin vendor/nmap/lib vendor/nmap/share
cp -L "$BIN" vendor/nmap/bin/nmap && cp -R "$DATA" vendor/nmap/share/nmap
ldd "$BIN" | awk '/=> \//{print $3}' | grep -vE '/libc\.so|/libm\.so|libpthread|/libdl\.|ld-linux|libgcc_s|libstdc\+\+|/librt\.|libresolv' | while read -r l; do cp -L "$l" vendor/nmap/lib/; done
patchelf --set-rpath '$ORIGIN/../lib' vendor/nmap/bin/nmap
for l in vendor/nmap/lib/*.so*; do patchelf --set-rpath '$ORIGIN' "$l" 2>/dev/null || true; done
cp /usr/share/doc/nmap/copyright vendor/nmap/LICENSE-nmap.txt 2>/dev/null || true
echo "bundled $(vendor/nmap/bin/nmap --version | head -1) -> vendor/nmap ($(du -sh vendor/nmap | cut -f1))"
