#!/bin/bash
# Build .dmg installer for macOS
# Usage: ./scripts/build_dmg.sh

set -e

VERSION="0.0.1"
BUNDLE_ID="com.lq201.clipboard-tool"
APP_NAME="Clipboard Tool"
DMG_NAME="${APP_NAME}-${VERSION}.dmg"
VOL_NAME="${APP_NAME} Installer"

cd "$(dirname "$0")/.."

# 1. Check/create dist directory
if [ ! -d "dist/clipboard-tool" ]; then
    echo "Error: dist/clipboard-tool/ not found. Run 'uv run pyinstaller clipboard-tool.spec' first."
    exit 1
fi

# 2. Install create-dmg if needed
if ! command -v create-dmg &> /dev/null; then
    echo "Installing create-dmg..."
    if ! command -v brew &> /dev/null; then
        echo "Error: Homebrew not found. Please install from https://brew.sh"
        exit 1
    fi
    brew install create-dmg
fi

# 3. Clean previous builds
rm -rf "dist/${APP_NAME}.app"
rm -f "dist/${DMG_NAME}"

# 4. Create .app bundle
mkdir -p "dist/${APP_NAME}.app/Contents/MacOS"
mkdir -p "dist/${APP_NAME}.app/Contents/Resources"

# Create launcher script
cat > "dist/${APP_NAME}.app/Contents/MacOS/${APP_NAME}" << EOF
#!/bin/bash
DIR="\$(cd "\$(dirname "\$0")" && pwd)"
"\$DIR/../../../clipboard-tool/clipboard-tool" "\$@"
EOF
chmod +x "dist/${APP_NAME}.app/Contents/MacOS/${APP_NAME}"

# Create Info.plist
cat > "dist/${APP_NAME}.app/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>${APP_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>${BUNDLE_ID}</string>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>${VERSION}</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.14</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# 5. Create .dmg
echo "Creating ${DMG_NAME}..."
mkdir -p dist/dmg-staging
cp -R "dist/${APP_NAME}.app" dist/dmg-staging/
ln -s /Applications dist/dmg-staging/Applications

create-dmg \
  --volname "${VOL_NAME}" \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "${APP_NAME}.app" 200 190 \
  --icon "Applications" 600 190 \
  --hide-extension "${APP_NAME}.app" \
  --app-drop-link 600 190 \
  --no-internet-enable \
  "dist/${DMG_NAME}" \
  dist/dmg-staging/

# 6. Cleanup
rm -rf dist/dmg-staging
rm -rf "dist/${APP_NAME}.app"

echo ""
echo "Build complete!"
echo "Output: dist/${DMG_NAME}"
echo ""
echo "To install:"
echo "  1. Open dist/${DMG_NAME}"
echo "  2. Drag '${APP_NAME}' to Applications folder"
