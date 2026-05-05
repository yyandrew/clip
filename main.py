# main.py
import os
import sys

# 强制输出到终端（无缓冲）
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buffering=1)

# 禁用 GVFS/GIO 模块加载，避免不同系统 glib 版本不兼容报错
os.environ['GIO_MODULE_DIR'] = ''

print("[DEBUG] main.py 开始执行", flush=True)

from PyQt6.QtWidgets import QApplication
from clip import ClipboardApp

print("[DEBUG] 导入完成，创建 QApplication", flush=True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    print("[DEBUG] QApplication 创建成功", flush=True)
    window = ClipboardApp()
    print("[DEBUG] ClipboardApp 创建成功", flush=True)
    window.show()
    print("[DEBUG] 窗口显示成功", flush=True)
    sys.exit(app.exec())
