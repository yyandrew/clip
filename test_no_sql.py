# test_no_sql.py - 不用数据库的测试
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

print("[TEST] 开始无数据库测试", flush=True)

from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                             QLineEdit, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt

app = QApplication(sys.argv)
print("[TEST] QApplication 创建成功", flush=True)

window = QMainWindow()
window.setWindowTitle("No SQL Test")
window.resize(450, 600)
window.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

central = QWidget()
layout = QVBoxLayout(central)

search = QLineEdit()
search.setPlaceholderText("搜索...")
layout.addWidget(search)

list_widget = QListWidget()
for i in range(10):
    item = QListWidgetItem(f"测试项 {i} - 这是一段测试文本内容")
    list_widget.addItem(item)
layout.addWidget(list_widget)

window.setCentralWidget(central)
print("[TEST] UI 创建成功", flush=True)

window.show()
print("[TEST] 窗口显示成功，请按下键盘按键测试...", flush=True)

exit_code = app.exec()
print(f"[TEST] 退出，码: {exit_code}", flush=True)
sys.exit(exit_code)
