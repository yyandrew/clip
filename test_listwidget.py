# test_listwidget.py - 测试 QListWidget
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

print("[TEST] 开始 QListWidget 测试", flush=True)

from PyQt6.QtWidgets import QApplication, QMainWindow, QListWidget, QListWidgetItem

app = QApplication(sys.argv)
print("[TEST] QApplication 创建成功", flush=True)

window = QMainWindow()
window.resize(400, 300)

list_widget = QListWidget()
window.setCentralWidget(list_widget)
print("[TEST] QListWidget 创建成功", flush=True)

# 添加测试项
for i in range(5):
    item = QListWidgetItem(f"测试项 {i}")
    list_widget.addItem(item)
print("[TEST] 添加测试项成功", flush=True)

window.show()
print("[TEST] 窗口显示成功，请按下键盘按键测试...", flush=True)

exit_code = app.exec()
print(f"[TEST] 退出，码: {exit_code}", flush=True)
sys.exit(exit_code)
