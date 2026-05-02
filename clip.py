import sys
import datetime
import base64
from io import BytesIO
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                             QLineEdit, QListWidget, QListWidgetItem, QLabel,
                             QSystemTrayIcon, QMenu, QToolTip)
from PyQt6.QtGui import QAction, QPixmap, QImage
from PyQt6.QtCore import Qt, QTimer, QSize, QByteArray, QBuffer, QIODevice
from PyQt6.QtSql import QSqlDatabase, QSqlQuery
from pynput.keyboard import Controller, Key

# 键盘控制器，用于模拟粘贴动作
keyboard = Controller()

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
        self.create_tray_icon()

    def init_db(self):
        db = QSqlDatabase.addDatabase("QSQLITE")
        db.setDatabaseName("clips_pro.db")
        db.open()
        query = QSqlQuery()
        # 增加 blob_data 字段存储图片二进制
        query.exec("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT, -- 'text' 或 'image'
                content TEXT, -- 文本内容或图片的预览摘要
                blob_data BLOB,
                timestamp DATETIME
            )
        """)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 搜索框
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 搜索历史 (支持实时过滤)...")
        self.search_bar.textChanged.connect(self.refresh_list)
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
        layout.addWidget(self.list_widget)

        self.status_label = QLabel("按 Enter 粘贴并隐藏")
        self.status_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self.status_label)

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
            query.prepare("INSERT INTO history (type, content, blob_data, timestamp) VALUES ('image', '[Image]', ?, ?)")
            query.addBindValue(raw_data)
            query.addBindValue(now)
            query.exec()

        elif mime_data.hasText():
            # 处理文本 (保持之前的逻辑)
            text = mime_data.text()
            if not text.strip(): return
            query.prepare("""
                INSERT INTO history (type, content, timestamp) VALUES ('text', ?, ?)
                ON CONFLICT(content) DO UPDATE SET timestamp = excluded.timestamp
            """)
            query.addBindValue(text)
            query.addBindValue(now)
            query.exec()

        self.refresh_list()

    def refresh_list(self):
        self.list_widget.clear()
        query = QSqlQuery("SELECT type, content, blob_data, timestamp FROM history ORDER BY timestamp DESC LIMIT 50")

        while query.next():
            c_type = query.value(0)
            content = query.value(1)
            blob = query.value(2)
            time_str = query.value(3)

            item = QListWidgetItem(self.list_widget)

            if c_type == 'image':
                # 如果是图片，列表显示图标和时间
                item.setText(f"🖼️ 图片记录 - {time_str}")
                # 关键：ToolTip 支持 HTML。我们将图片转为 Base64 嵌入 HTML
                pixmap = QPixmap()
                pixmap.loadFromData(blob)
                # 缩放图片用于预览，避免悬浮窗太大
                scaled_pix = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio)

                # 将缩放后的图片转为 Base64 字符串
                ba = QByteArray()
                bu = QBuffer(ba)
                bu.open(QIODevice.OpenModeFlag.WriteOnly)
                scaled_pix.save(bu, "PNG")
                b64 = ba.toBase64().data().decode()

                item.setToolTip(f'<html><body><img src="data:image/png;base64,{b64}" /><br/>{time_str}</body></html>')
            else:
                # 如果是文本
                short_text = content[:50].replace('\n', ' ')
                item.setText(f"📄 {short_text}\n[{time_str}]")
                # 文本的 ToolTip
                item.setToolTip(f"完整内容:\n{content}")

            self.list_widget.addItem(item)

    def eventFilter(self, source, event):
        # 让搜索框支持上下箭头切换列表项
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
        return super().eventFilter(source, event)

    def paste_selected_item(self):
        current_item = self.list_widget.currentItem()
        if not current_item: return

        # 1. 拿到原始文本
        text_to_paste = current_item.data(Qt.ItemDataRole.UserRole)

        # 2. 先写回剪切板 (为了确保粘贴的是我们选中的)
        self.clipboard.setText(text_to_paste)

        # 3. 隐藏窗口
        self.hide()

        # 4. 模拟粘贴动作 (延迟一小会儿确保焦点切回原应用)
        # 这就像 Go 里的 time.AfterFunc
        QTimer.singleShot(100, lambda: self.simulate_paste())

    def simulate_paste(self):
        # 模拟键盘按键 Ctrl+V (Windows/Linux) 或 Cmd+V (Mac)
        with keyboard.pressed(Key.ctrl if sys.platform != 'darwin' else Key.cmd):
            keyboard.press('v')
            keyboard.release('v')
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
