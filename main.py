# main.py
import os
import sys

# 强制输出到终端（无缓冲）
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buffering=1)

print("[DEBUG] main.py 开始执行", flush=True)

# PyInstaller 打包后设置 Qt 插件路径
if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
    print(f"[DEBUG] PyInstaller 模式，基础目录: {base_dir}", flush=True)
    
    # 设置平台插件路径
    qt_plugin_paths = [
        os.path.join(base_dir, 'PyQt6', 'Qt6', 'plugins'),
        os.path.join(base_dir, 'qt6_plugins'),
        os.path.join(base_dir, 'plugins'),
    ]
    for plugin_path in qt_plugin_paths:
        if os.path.exists(plugin_path):
            print(f"[DEBUG] 设置 QT_PLUGIN_PATH: {plugin_path}", flush=True)
            os.environ['QT_PLUGIN_PATH'] = plugin_path
            break
    
    # 检查平台插件
    platforms_dir = os.path.join(os.environ.get('QT_PLUGIN_PATH', ''), 'platforms')
    if os.path.exists(platforms_dir):
        print(f"[DEBUG] 平台插件目录: {platforms_dir}", flush=True)
        for f in os.listdir(platforms_dir):
            print(f"[DEBUG]   - {f}", flush=True)
    else:
        print(f"[WARN] 找不到平台插件目录", flush=True)
        # 搜索所有 platforms 目录
        for root, dirs, files in os.walk(base_dir):
            if 'platforms' in dirs:
                print(f"[DEBUG] 找到 platforms: {os.path.join(root, 'platforms')}", flush=True)

# 禁用 GVFS/GIO 模块加载
os.environ['GIO_MODULE_DIR'] = ''

print("[DEBUG] 导入 PyQt6...", flush=True)

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
    print("[DEBUG] 进入事件循环...", flush=True)
    exit_code = app.exec()
    print(f"[DEBUG] 事件循环结束，退出码: {exit_code}", flush=True)
    sys.exit(exit_code)
