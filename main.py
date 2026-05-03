# main.py
import sys
from PyQt6.QtWidgets import QApplication
from clip import ClipboardApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ClipboardApp()
    window.show()
    sys.exit(app.exec())
