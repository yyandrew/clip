import sys
import datetime
import base64
from io import BytesIO
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                             QLineEdit, QListWidget, QListWidgetItem, QLabel,
                             QSystemTrayIcon, QMenu, QToolTip)
from PyQt6.QtGui import QAction, QPixmap, QImage
from PyQt6.QtCore import Qt, QTimer, QSize, QByteArray, QBuffer, QIODevice
from pynput.keyboard import Controller, Key

# 键盘控制器，用于模拟粘贴动作
keyboard = Controller()

class ClipboardApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pro Clipboard (No SQL)")
        self.setFixedSize(450, 600)
        # 设置窗口置顶，类似常用的剪切板工具
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

        self.history = []  # 内存存储替代数据库
        self.setup_ui()

        # 监听剪切板
        self.clipboard = QApplication.clipboard()
        self.clipboard.dataChanged.connect(self.handle_clipboard_change)

        # 初始加载
        self.refresh_list()
        self.create_tray_icon()

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

        if mime_data.hasImage():
            # 处理图片
            image = self.clipboard.image()
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            image.save(buffer, "PNG")
            raw_data = byte_array.data()

            self.history.insert(0, {
                'type': 'image',
                'content': '[Image]',
                'blob_data': raw_data,
                'timestamp': now
            })

        elif mime_data.hasText():
            # 处理文本
            text = mime_data.text()
            if not text.strip(): return
            
            # 去重：如果已存在相同文本，更新时间并移到顶部
            existing = None
            for i, item in enumerate(self.history):
                if item['type'] == 'text' and item['content'] == text:
                    existing = i
                    break
            
            if existing is not None:
                self.history.pop(existing)
            
            self.history.insert(0, {
                'type': 'text',
                'content': text,
                'blob_data': None,
                'timestamp': now
            })

        # 限制历史记录数量
        self.history = self.history[:50]
        self.refresh_list()

    def _on_search_text_changed(self, text):
        """防抖处理搜索输入"""
        self._pending_search_text = text
        self.search_timer.start(300)  # 300ms 防抖

    def _do_refresh(self):
        """执行实际的搜索刷新"""
        self.refresh_list(getattr(self, '_pending_search_text', ''))

    def refresh_list(self, search_text=""):
        self.list_widget.clear()
        
        items = self.history
        if search_text:
            items = [item for item in items if search_text.lower() in (item['content'] or '').lower()]
        
        # 只显示前50条
        items = items[:50]

        for item_data in items:
            c_type = item_data['type']
            content = item_data['content']
            blob = item_data['blob_data']
            time_str = item_data['timestamp']

            item = QListWidgetItem(self.list_widget)

            if c_type == 'image':
                # 如果是图片，列表显示图标和时间
                item.setText(f"🖼️ 图片记录 - {time_str}")
                item.setData(Qt.ItemDataRole.UserRole, f"image:{time_str}")
                
                try:
                    pixmap = QPixmap()
                    if not pixmap.loadFromData(blob):
                        item.setToolTip("图片格式无效")
                        self.list_widget.addItem(item)
                        continue
                    
                    if pixmap.isNull():
                        item.setToolTip("图片数据为空")
                        self.list_widget.addItem(item)
                        continue
                    
                    scaled_pix = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio)
                    if scaled_pix.isNull():
                        item.setToolTip("图片处理失败")
                        self.list_widget.addItem(item)
                        continue

                    ba = QByteArray()
                    bu = QBuffer(ba)
                    bu.open(QIODevice.OpenModeFlag.WriteOnly)
                    if not scaled_pix.save(bu, "PNG"):
                        item.setToolTip("图片编码失败")
                        self.list_widget.addItem(item)
                        continue
                    b64 = ba.toBase64().data().decode()

                    item.setToolTip(f'<html><body><img src="data:image/png;base64,{b64}" /><br/>{time_str}</body></html>')
                except Exception as e:
                    print(f"[ERROR] 图片预览生成失败: {e}")
                    item.setToolTip("图片预览生成失败")
                self.list_widget.addItem(item)
            else:
                # 如果是文本
                short_text = content[:30].replace('\n', ' ') if content else ''
                if content and len(content) > 30:
                    short_text += '...'
                item.setText(f"📄 {short_text}\n[{time_str}]")
                item.setData(Qt.ItemDataRole.UserRole, f"text:{content}")
                item.setToolTip(f"完整内容:\n{content}")
                self.list_widget.addItem(item)

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
        if isinstance(role_data, str) and role_data.startswith('text:'):
            text_to_paste = role_data[5:]
        else:
            return

        # 2. 先写回剪切板 (为了确保粘贴的是我们选中的)
        self.clipboard.setText(text_to_paste)

        # 3. 隐藏窗口
        self.hide()

        # 4. 模拟粘贴动作 (延迟一小会儿确保焦点切回原应用)
        QTimer.singleShot(300, lambda: self.simulate_paste())

    def delete_selected_item(self):
        current_item = self.list_widget.currentItem()
        if not current_item: return

        role_data = current_item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(role_data, str): return

        if role_data.startswith('text:'):
            value = role_data[5:]
            self.history = [item for item in self.history if not (item['type'] == 'text' and item['content'] == value)]
        elif role_data.startswith('image:'):
            value = role_data[6:]
            self.history = [item for item in self.history if not (item['type'] == 'image' and item['timestamp'] == value)]
        else:
            return

        row = self.list_widget.currentRow()
        self.list_widget.takeItem(row)

    def simulate_paste(self):
        # 模拟键盘按键 Ctrl+V (Windows/Linux) 或 Cmd+V (Mac)
        try:
            with keyboard.pressed(Key.ctrl if sys.platform != 'darwin' else Key.cmd):
                keyboard.press('v')
                keyboard.release('v')
        except Exception:
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
