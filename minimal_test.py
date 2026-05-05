# minimal_test.py - 最小化 Qt 测试
import os
import sys

sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buffering=1)

if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
    plugin_path = os.path.join(base_dir, 'PyQt6', 'Qt6', 'plugins')
    if os.path.exists(plugin_path):
        os.environ['QT_PLUGIN_PATH'] = plugin_path

os.environ['GIO_MODULE_DIR'] = ''

print("[TEST] 开始最小化 Qt 测试", flush=True)

from PyQt6.QtWidgets import QApplication, QMainWindow

app = QApplication(sys.argv)
print("[TEST] QApplication 创建成功", flush=True)

window = QMainWindow()
window.setWindowTitle("Minimal Test")
window.resize(400, 300)
print("[TEST] QMainWindow 创建成功", flush=True)

window.show()
print("[TEST] 窗口显示成功", flush=True)
print("[TEST] 进入事件循环，请按下键盘按键测试...", flush=True)

exit_code = app.exec()
print(f"[TEST] 正常退出，码: {exit_code}", flush=True)
sys.exit(exit_code)
