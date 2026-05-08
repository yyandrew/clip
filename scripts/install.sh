#!/bin/bash
# Install clipboard-tool to ~/.local/ (no sudo required)
# Usage: ./scripts/install.sh

set -e

APP_NAME="clipboard-tool"
INSTALL_DIR="${HOME}/.local/lib/${APP_NAME}"
BIN_DIR="${HOME}/.local/bin"
SOURCE_DIR="$(cd "$(dirname "$0")/.." && pwd)/dist/${APP_NAME}"

echo "Installing ${APP_NAME}..."

# 1. Check if dist exists
if [ ! -d "${SOURCE_DIR}" ]; then
    echo "Error: ${SOURCE_DIR} not found."
    echo "Please run 'uv run pyinstaller clipboard-tool.spec' first."
    exit 1
fi

# 2. Create directories
mkdir -p "${INSTALL_DIR}"
mkdir -p "${BIN_DIR}"

# 3. Copy files
echo "Copying files to ${INSTALL_DIR}..."
cp -R "${SOURCE_DIR}/"* "${INSTALL_DIR}/"

# 4. Create symlink
echo "Creating symlink in ${BIN_DIR}..."
ln -sf "${INSTALL_DIR}/${APP_NAME}" "${BIN_DIR}/${APP_NAME}"

# 5. Check PATH
echo ""
if [[ ":${PATH}:" != *":${BIN_DIR}:"* ]]; then
    echo "WARNING: ${BIN_DIR} is not in your PATH."
    echo ""
    echo "Add one of these to your shell profile (~/.bashrc, ~/.zshrc, etc.):"
    echo "  export PATH=\"\${HOME}/.local/bin:\${PATH}\""
    echo ""
    echo "Then reload:"
    echo "  source ~/.bashrc  # or ~/.zshrc"
fi

echo ""
echo "Installation complete!"
echo "Run with: ${APP_NAME}"
echo ""
echo "To uninstall:"
echo "  rm -rf ${INSTALL_DIR}"
echo "  rm ${BIN_DIR}/${APP_NAME}"
