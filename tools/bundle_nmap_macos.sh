#!/bin/sh
# Copies the Homebrew nmap into vendor/nmap/ as a relocatable bundle:
#   vendor/nmap/bin/nmap        (install names rewritten to @executable_path/../lib)
#   vendor/nmap/lib/*.dylib     (openssl, libssh2, pcre2, liblinear, lua + their deps)
#   vendor/nmap/share/nmap/*    (nmap-services, nmap-os-db, nmap-mac-prefixes, NSE scripts…)
# nmap is distributed under the Nmap Public Source License – see THIRD_PARTY_NOTICES.md
set -e
cd "$(dirname "$0")/.."
SRC=${NMAP_PREFIX:-$(brew --prefix nmap 2>/dev/null || echo /opt/homebrew/opt/nmap)}
OUT=vendor/nmap
rm -rf "$OUT" && mkdir -p "$OUT/bin" "$OUT/lib" "$OUT/share"
cp "$SRC/bin/nmap" "$OUT/bin/nmap"
cp -R "$SRC/share/nmap" "$OUT/share/nmap"
chmod -R u+w "$OUT"

# recursive dylib collection
queue="$OUT/bin/nmap"
while [ -n "$queue" ]; do
  next=""
  for f in $queue; do
    for dep in $(otool -L "$f" | tail -n +2 | awk '{print $1}' | grep -E '^/(opt/homebrew|usr/local)/'); do
      base=$(basename "$dep")
      if [ ! -f "$OUT/lib/$base" ]; then
        cp "$(readlink -f "$dep")" "$OUT/lib/$base"; chmod u+w "$OUT/lib/$base"
        next="$next $OUT/lib/$base"
      fi
      install_name_tool -change "$dep" "@executable_path/../lib/$base" "$f" 2>/dev/null || \
      install_name_tool -change "$dep" "@loader_path/$base" "$f"
    done
  done
  queue="$next"
done
# lib -> lib references use @loader_path; binary -> lib uses @executable_path/../lib
for l in "$OUT"/lib/*.dylib; do
  install_name_tool -id "@loader_path/$(basename "$l")" "$l"
  for dep in $(otool -L "$l" | tail -n +2 | awk '{print $1}' | grep -E '^@executable_path'); do
    install_name_tool -change "$dep" "@loader_path/$(basename "$dep")" "$l"
  done
done
codesign --force --sign - "$OUT"/lib/*.dylib "$OUT/bin/nmap" 2>/dev/null || true
cp "$SRC/COPYING" "$OUT/LICENSE-nmap.txt" 2>/dev/null || cp "$SRC/LICENSE" "$OUT/LICENSE-nmap.txt" 2>/dev/null || true
echo "bundled nmap $($OUT/bin/nmap --version | head -1) -> $OUT ($(du -sh $OUT | cut -f1))"
otool -L "$OUT/bin/nmap" | grep -c homebrew | xargs -I{} sh -c '[ {} = 0 ] && echo "no homebrew paths left – relocatable" || echo "WARNING: homebrew paths remain"'
