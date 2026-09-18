#!/bin/sh
# Self-contained desktop app with PyInstaller, nmap included (no Python, no nmap install needed on the target).
#   macOS   -> dist/app/WifiScan.app  + dist/WifiScan-macos-<arch>.zip
#   Windows -> dist/app/WifiScan/     + zip   (run tools/bundle_nmap_windows.sh first)
#   Linux   -> dist/app/WifiScan/     + tar.gz (run tools/bundle_nmap_linux.sh first)
# Needs: pip install pyinstaller ; and vendor/nmap/ prepared by tools/bundle_nmap_<os>.sh
set -e
cd "$(dirname "$0")"
[ -x vendor/nmap/bin/nmap ] || [ -f vendor/nmap/bin/nmap.exe ] || { echo "vendor/nmap missing – run tools/bundle_nmap_<os>.sh first (or set SKIP_NMAP=1)"; [ -n "$SKIP_NMAP" ] || exit 1; }
mkdir -p build dist
printf 'import sys\nfrom wifiscan.cli import main\nsys.exit(main())\n' > build/entry.py
VER=$(python3 -c 'import wifiscan;print(wifiscan.__version__)')
case "$(uname -s)" in
  Darwin) ICON="$(pwd)/assets/wifiscan.icns"; OS=macos ;;
  MINGW*|MSYS*|CYGWIN*|Windows_NT) ICON="$(pwd)/assets/wifiscan.ico"; OS=windows ;;
  *) ICON="$(pwd)/assets/icon_256.png"; OS=linux ;;
esac
PYI=${PYINSTALLER:-pyinstaller}
ADD=""; [ -d vendor/nmap ] && ADD="--add-data $(pwd)/vendor/nmap:nmap"
[ "$OS" = windows ] && [ -d vendor/nmap ] && ADD="--add-data $(pwd)/vendor/nmap;nmap"
$PYI --onedir --windowed --name WifiScan --icon "$ICON" --clean --noconfirm --paths . $ADD \
     --osx-bundle-identifier hu.krisz.wifiscan \
     --distpath dist/app --workpath build/pyi-app --specpath build build/entry.py
if [ "$OS" = macos ]; then
  APP=dist/app/WifiScan.app
  /usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $VER" "$APP/Contents/Info.plist" || true
  # PyInstaller puts --add-data under Contents/Resources on macOS and symlinks from Frameworks; make nmap executable
  chmod +x "$APP"/Contents/Resources/nmap/bin/nmap "$APP"/Contents/Frameworks/nmap/bin/nmap 2>/dev/null || true
  codesign --force --deep --sign - "$APP" 2>/dev/null || true
  ZIP="dist/WifiScan-macos-$(uname -m).zip"; rm -f "$ZIP" && (cd dist/app && ditto -c -k --keepParent WifiScan.app "../$(basename "$ZIP")")
  echo "built $APP and $ZIP ($(du -sh "$ZIP" | cut -f1))"
elif [ "$OS" = windows ]; then
  (cd dist/app && powershell -c "Compress-Archive -Force WifiScan ../WifiScan-windows-x64.zip") && echo "built dist/WifiScan-windows-x64.zip"
else
  (cd dist/app && tar czf "../WifiScan-linux-$(uname -m).tar.gz" WifiScan) && echo "built dist/WifiScan-linux-$(uname -m).tar.gz"
fi
