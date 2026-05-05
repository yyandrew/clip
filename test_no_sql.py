# test_no_sql.py
import os
import sys

# 禁用 GVFS/GIO 模块加载，避免不同系统 glib 版本不兼容报错
os.environ['GIO_MODULE_DIR'] = ''

from PyQt6.QtWidgets import QApplication
from clip_no_sql import ClipboardApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ClipboardApp()
    window.show()
    sys.exit(app.exec())
