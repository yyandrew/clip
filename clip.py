import sys
import ast
import datetime
import base64
import traceback
import logging
from io import BytesIO
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                             QLineEdit, QListWidget, QListWidgetItem, QLabel,
                             QSystemTrayIcon, QMenu, QToolTip)
from PyQt6.QtGui import QAction, QPixmap, QImage
from PyQt6.QtCore import Qt, QTimer, QSize, QByteArray, QBuffer, QIODevice, qInstallMessageHandler
from PyQt6.QtSql import QSqlDatabase, QSqlQuery
from pynput.keyboard import Controller, Key

# 键盘控制器，用于模拟粘贴动作
keyboard = Controller()

def debug_print(msg):
    """强制打印到 stderr"""
    print(msg, file=sys.stderr, flush=True)

class ClipboardApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pro Clipboard")
        self.setFixedSize(450, 600)
        # 设置窗口置顶，类似常用的剪切板工具
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

        self.init_db()
        self.setup_ui()

        # 监听剪切板
        self.clipboard = QApplication.clipboard()
        self.clipboard.dataChanged.connect(self.handle_clipboard_change)

        # 初始加载
        self.refresh_list()
        debug_print("[DEBUG] 跳过托盘图标初始化（调试模式）")
        # self.create_tray_icon()

    def init_db(self):
        import os
        config_dir = os.path.expanduser("~/.config/clip")
        os.makedirs(config_dir, exist_ok=True)
        db_path = os.path.join(config_dir, "clips_pro.db")
        print(f"[DEBUG] 数据库路径: {db_path}")
        db = QSqlDatabase.addDatabase("QSQLITE")
        db.setDatabaseName(db_path)
        db.open()
        query = QSqlQuery()
        # 增加 blob_data 字段存储图片二进制
        # content 必须是 UNIQUE 才能支持 ON CONFLICT
        ok = query.exec("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT,
                content TEXT UNIQUE,
                blob_data BLOB,
                timestamp DATETIME
            )
        """)
        if not ok:
            print(f"[ERROR] 建表失败: {query.lastError().text()}")
        else:
            # 验证表结构
            check = QSqlQuery("PRAGMA index_list(history)")
            print("[DEBUG] history 表索引:")
            while check.next():
                print(f"  - {check.value(1)} (unique={check.value(2)})")

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 搜索框
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 搜索历史 (支持实时过滤)...")
        # 添加防抖计时器，避免输入过快频繁刷新
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._do_refresh)
        self.search_bar.textChanged.connect(self._on_search_text_changed)
        # 让搜索框拦截上下箭头，方便直接操作列表
        self.search_bar.installEventFilter(self)
        layout.addWidget(self.search_bar)

        # 列表
        self.list_widget = QListWidget()
        # 优化列表样式
        self.list_widget.setStyleSheet("""
            QListWidget::item { border-bottom: 1px solid #eee; padding: 10px; }
            QListWidget::item:selected { background: #e3f2fd; color: #1976d2; }
        """)
        self.list_widget.installEventFilter(self)
        layout.addWidget(self.list_widget)

        self.statusBar().showMessage("按 Enter 粘贴并隐藏")

    def handle_clipboard_change(self):
        mime_data = self.clipboard.mimeData()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = QSqlQuery()

        if mime_data.hasImage():
            # 处理图片
            image = self.clipboard.image()
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            image.save(buffer, "PNG")
            raw_data = byte_array.data()

            # 使用内容摘要作为唯一标识（简单起见用哈希或跳过重复检测）
            ok = query.prepare("INSERT INTO history (type, content, blob_data, timestamp) VALUES ('image', '[Image]', ?, ?)")
            if not ok:
                print(f"[ERROR] 图片 prepare 失败: {query.lastError().text()}")
                return
            # 必须绑定 QByteArray，若绑定 Python bytes 会被 SQLite 驱动误存为 str
            query.addBindValue(byte_array)
            query.addBindValue(now)
            query.exec()

        elif mime_data.hasText():
            # 处理文本 (保持之前的逻辑)
            text = mime_data.text()
            if not text.strip(): return
            ok = query.prepare(
                "INSERT INTO history (type, content, timestamp) VALUES ('text', ?, ?) "
                "ON CONFLICT(content) DO UPDATE SET timestamp = excluded.timestamp"
            )
            if not ok:
                print(f"[ERROR] prepare 失败: {query.lastError().text()}")
                return
            query.addBindValue(text)
            query.addBindValue(now)
            if not query.exec():
                print(f"[ERROR] 文本插入失败: {query.lastError().text()}")
            else:
                print(f"[DEBUG] 文本插入成功: {text[:50]}")

        self.refresh_list()

    def _on_search_text_changed(self, text):
        """防抖处理搜索输入"""
        self._pending_search_text = text
        self.search_timer.start(300)  # 300ms 防抖

    def _do_refresh(self):
        """执行实际的搜索刷新"""
        self.refresh_list(getattr(self, '_pending_search_text', ''))

    def refresh_list(self, search_text=""):
        debug_print(f"[DEBUG] refresh_list 开始，搜索词: '{search_text}'")
        self.list_widget.clear()
        if search_text:
            debug_print("[DEBUG] 执行搜索 SQL")
            query = QSqlQuery()
            query.prepare("SELECT type, content, blob_data, timestamp FROM history WHERE content LIKE ? ORDER BY timestamp DESC LIMIT 50")
            query.addBindValue(f"%{search_text}%")
            if not query.exec():
                debug_print(f"[ERROR] 搜索失败: {query.lastError().text()}")
                return
        else:
            debug_print("[DEBUG] 执行全量 SQL")
            query = QSqlQuery("SELECT type, content, blob_data, timestamp FROM history ORDER BY timestamp DESC LIMIT 50")

        row_count = 0
        debug_print("[DEBUG] 开始遍历结果")
        while query.next():
            row_count += 1
            try:
                c_type = query.value(0)
                content = query.value(1)
                blob = query.value(2)
                time_str = query.value(3)
                
                # 调试：打印每行数据的类型
                print(f"[DEBUG] row {row_count}: type={c_type}, content_type={type(content)}, blob_type={type(blob)}, blob_len={len(blob) if blob else 0}")

                item = QListWidgetItem(self.list_widget)

                if c_type == 'image':
                    debug_print(f"[DEBUG] 处理图片行 {row_count}")
                    item.setText(f"🖼️ 图片记录 - {time_str}")
                    item.setData(Qt.ItemDataRole.UserRole, ('image', time_str))
                    
                    # 临时跳过图片预览，测试是否导致崩溃
                    item.setToolTip("图片预览已禁用（调试模式）")
                    self.list_widget.addItem(item)
                    continue
                    
                    # 严格检查 blob 是否有效
                    if blob is None:
                        print("[WARN] blob is None")
                        item.setToolTip("图片数据缺失")
                        self.list_widget.addItem(item)
                        continue
                    
                    # 处理 PyQt6 QVariant 或空值
                    blob_bytes = None
                    if hasattr(blob, 'toByteArray'):
                        blob_bytes = blob.toByteArray()
                    elif isinstance(blob, (bytes, bytearray)):
                        blob_bytes = bytes(blob)
                    elif isinstance(blob, str):
                        try:
                            blob_bytes = ast.literal_eval(blob)
                        except Exception:
                            print("[WARN] blob str 解析失败")
                            item.setToolTip("图片数据损坏")
                            self.list_widget.addItem(item)
                            continue
                    else:
                        print(f"[WARN] blob 类型不支持: {type(blob)}")
                        item.setToolTip("图片数据类型错误")
                        self.list_widget.addItem(item)
                        continue
                    
                    if not blob_bytes or len(blob_bytes) == 0:
                        print("[WARN] blob_bytes 为空")
                        item.setToolTip("图片数据为空")
                        self.list_widget.addItem(item)
                        continue
                    
                    try:
                        pixmap = QPixmap()
                        if not pixmap.loadFromData(blob_bytes):
                            print("[WARN] 无法加载图片数据")
                            item.setToolTip("图片格式无效")
                            self.list_widget.addItem(item)
                            continue
                        
                        if pixmap.isNull():
                            print("[WARN] 图片数据为空")
                            item.setToolTip("图片数据为空")
                            self.list_widget.addItem(item)
                            continue
                        
                        scaled_pix = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio)
                        if scaled_pix.isNull():
                            print("[WARN] 图片缩放失败")
                            item.setToolTip("图片处理失败")
                            self.list_widget.addItem(item)
                            continue

                        ba = QByteArray()
                        bu = QBuffer(ba)
                        bu.open(QIODevice.OpenModeFlag.WriteOnly)
                        if not scaled_pix.save(bu, "PNG"):
                            print("[WARN] 图片编码失败")
                            item.setToolTip("图片编码失败")
                            self.list_widget.addItem(item)
                            continue
                        b64 = ba.toBase64().data().decode()

                        item.setToolTip(f'<html><body><img src="data:image/png;base64,{b64}" /><br/>{time_str}</body></html>')
                    except Exception as e:
                        print(f"[ERROR] 图片预览生成失败: {e}")
                        import traceback
                        traceback.print_exc()
                        item.setToolTip("图片预览生成失败")
                    self.list_widget.addItem(item)
                else:
                    short_text = content[:30].replace('\n', ' ') if content else ''
                    if content and len(content) > 30:
                        short_text += '...'
                    item.setText(f"📄 {short_text}\n[{time_str}]")
                    item.setData(Qt.ItemDataRole.UserRole, ('text', content))
                    item.setToolTip(f"完整内容:\n{content}")
                    self.list_widget.addItem(item)
            except Exception as e:
                print(f"[ERROR] 处理第 {row_count} 行时出错: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"[DEBUG] refresh_list 完成，共 {row_count} 行")

    def eventFilter(self, source, event):
        # 让搜索框支持上下箭头切换列表项，列表支持 Enter 粘贴
        if event.type() == event.Type.KeyPress and source is self.search_bar:
            if event.key() == Qt.Key.Key_Down:
                self.list_widget.setCurrentRow(min(self.list_widget.currentRow() + 1, self.list_widget.count() - 1))
                return True
            elif event.key() == Qt.Key.Key_Up:
                self.list_widget.setCurrentRow(max(self.list_widget.currentRow() - 1, 0))
                return True
            elif event.key() == Qt.Key.Key_Return:
                self.paste_selected_item()
                return True
        elif event.type() == event.Type.KeyPress and source is self.list_widget and event.key() == Qt.Key.Key_Return:
            self.paste_selected_item()
            return True
        elif event.type() == event.Type.KeyPress and source is self.list_widget and event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            self.delete_selected_item()
            return True
        return super().eventFilter(source, event)

    def paste_selected_item(self):
        current_item = self.list_widget.currentItem()
        if not current_item: return

        # 1. 拿到原始文本
        role_data = current_item.data(Qt.ItemDataRole.UserRole)
        if isinstance(role_data, tuple) and role_data[0] == 'text':
            text_to_paste = role_data[1]
        else:
            return

        # 2. 先写回剪切板 (为了确保粘贴的是我们选中的)
        self.clipboard.setText(text_to_paste)

        # 3. 隐藏窗口
        self.hide()

        # 4. 模拟粘贴动作 (延迟一小会儿确保焦点切回原应用)
        # 这就像 Go 里的 time.AfterFunc
        QTimer.singleShot(300, lambda: self.simulate_paste())

    def delete_selected_item(self):
        current_item = self.list_widget.currentItem()
        if not current_item: return

        role_data = current_item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(role_data, tuple): return

        item_type, value = role_data
        query = QSqlQuery()
        if item_type == 'text':
            query.prepare("DELETE FROM history WHERE content = ?")
            query.addBindValue(value)
        elif item_type == 'image':
            query.prepare("DELETE FROM history WHERE type = 'image' AND timestamp = ?")
            query.addBindValue(value)
        else:
            return

        if query.exec():
            row = self.list_widget.currentRow()
            self.list_widget.takeItem(row)
        else:
            print(f"[ERROR] 删除失败: {query.lastError().text()}")

    def simulate_paste(self):
        # 模拟键盘按键 Ctrl+V (Windows/Linux) 或 Cmd+V (Mac)
        try:
            with keyboard.pressed(Key.ctrl if sys.platform != 'darwin' else Key.cmd):
                keyboard.press('v')
                keyboard.release('v')
        except Exception as e:
            pass

    def create_tray_icon(self):
        # 1. 创建托盘图标对象
        self.tray_icon = QSystemTrayIcon(self)

        # 注意：你需要一个 .png 或 .ico 图标文件。
        # 如果没有，暂时可以用系统自带图标演示：
        self.tray_icon.setIcon(QApplication.style().standardIcon(
            QApplication.style().StandardPixmap.SP_ComputerIcon
        ))

        # 2. 创建托盘菜单
        tray_menu = QMenu()

        show_action = QAction("显示窗口", self)
        show_action.triggered.connect(self.show_normal) # 恢复显示

        quit_action = QAction("完全退出", self)
        quit_action.triggered.connect(QApplication.instance().quit)

        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        # 3. 设置菜单并显示图标
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        # 4. 响应左键双击/单击托盘
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger: # 单击
            self.show_normal()

    def show_normal(self):
        self.show()
        self.activateWindow() # 强制获取焦点
        self.raise_()         # 移至顶层

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ClipboardApp()
    window.show()
    sys.exit(app.exec())
