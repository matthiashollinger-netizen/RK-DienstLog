#!/bin/bash
set -e

VERSION=$(python3 -c "import json; print(json.load(open('version.json', encoding='utf-8'))['version'])")

cat > update.json << EOF
{
  "version": "$VERSION",
  "mac_zip_url": "https://github.com/matthiashollinger-netizen/RK-DienstLog/releases/download/v$VERSION/RK_DienstLog_${VERSION}_mac.zip",
  "windows_url": "https://github.com/matthiashollinger-netizen/RK-DienstLog/releases/download/v$VERSION/RK_DienstLog_Setup_${VERSION}.exe",
  "changelog": [
    "Bitte Changelog fuer Version $VERSION eintragen"
  ]
}
EOF

echo "update.json fuer Version $VERSION erstellt."
