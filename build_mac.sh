 #!/bin/bash
set -e

APP_NAME="RK DienstLog"
VERSION=$(python3 -c "import json; print(json.load(open('version.json', encoding='utf-8'))['version'])")

echo "========================================"
echo "Baue $APP_NAME Version $VERSION für macOS"
echo "========================================"

rm -rf build dist
rm -f "RK_DienstLog_${VERSION}.dmg"
rm -f "RK_DienstLog_${VERSION}_mac.zip"

pyinstaller "RK DienstLog.spec"

chmod +x "dist/RK DienstLog.app/Contents/MacOS/RK DienstLog"

echo "Erstelle Auto-Update ZIP..."
cd dist
ditto -c -k --sequesterRsrc --keepParent \
"RK DienstLog.app" \
"RK_DienstLog_${VERSION}_mac.zip"
cd ..

echo "Erstelle DMG..."
create-dmg \
  --volname "RK DienstLog" \
  --volicon "rk_dienstlog.icns" \
  --background "rk_dienstlog_dmg_background_clean.png" \
  --window-pos 200 120 \
  --window-size 760 440 \
  --icon-size 112 \
  --icon "RK DienstLog.app" 190 245 \
  --app-drop-link 570 245 \
  "RK_DienstLog_${VERSION}.dmg" \
  "dist/RK DienstLog.app"

echo ""
echo "Fertig:"
echo "DMG: RK_DienstLog_${VERSION}.dmg"
echo "ZIP: dist/RK_DienstLog_${VERSION}_mac.zip"
