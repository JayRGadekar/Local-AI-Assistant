from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLineEdit, QTextEdit, 
    QApplication, QLabel, QGraphicsDropShadowEffect, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QFont, QPalette

from ui.worker import AgentWorker

class MainWindow(QMainWindow):
    def __init__(self, agent_executor):
        super().__init__()
        self.agent_executor = agent_executor
        
        # Window Flags
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.resize(800, 600)
        self.center()
        
        self.init_ui()
        self.worker = None
        self.chat_history = []
        self.drag_position = None

    def init_ui(self):
        # Central Widget
        self.central_widget = QWidget()
        self.central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(self.central_widget)
        
        # Layout
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        
        # Stylesheet
        self.setStyleSheet("""
            QWidget#CentralWidget {
                background-color: rgba(30, 30, 30, 240);
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 30);
            }
            QLineEdit {
                background-color: rgba(50, 50, 50, 255);
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 16px;
                selection-background-color: #3D8EC9;
            }
            QTextEdit {
                background-color: transparent;
                color: #DDDDDD;
                border: none;
                font-size: 14px;
                line-height: 1.5;
            }
            QLabel {
                color: #AAAAAA;
                font-size: 12px;
            }
            QPushButton#CloseButton {
                background-color: transparent;
                color: #888888;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton#CloseButton:hover {
                color: #FF5555;
            }
            QPushButton#MinimizeButton {
                background-color: transparent;
                color: #888888;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton#MinimizeButton:hover {
                color: #DDDDDD;
            }
        """)

        # Drop Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 150))
        self.central_widget.setGraphicsEffect(shadow)

        # Top Bar Layout
        self.top_layout = QHBoxLayout()
        self.top_layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addLayout(self.top_layout)

        # Spacer
        self.top_layout.addStretch()

        # Minimize Button
        self.min_btn = QPushButton("—")
        self.min_btn.setObjectName("MinimizeButton")
        self.min_btn.setFixedSize(30, 30)
        self.min_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.min_btn.clicked.connect(self.showMinimized)
        self.top_layout.addWidget(self.min_btn)

        # Close Button
        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("CloseButton")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.clicked.connect(QApplication.instance().quit)
        self.top_layout.addWidget(self.close_btn)

        # Input Field
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ask me anything... (e.g., 'Summarize the Amazon JD')")
        self.search_input.returnPressed.connect(self.process_query)
        self.layout.addWidget(self.search_input)

        # Loading Label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.status_label)
        self.status_label.hide()

        # Output Area
        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        self.layout.addWidget(self.result_area)

    def center(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def process_query(self):
        query = self.search_input.text().strip()
        if not query:
            return

        # Command to close app
        if query.lower() in ['quit', 'exit']:
            QApplication.instance().quit()
            return

        self.append_message("You", query)
        self.chat_history.append(("user", query))
        
        self.search_input.clear()
        self.search_input.setDisabled(True)
        self.status_label.setText("Thinking...")
        self.status_label.show()
        
        # Start Async Worker with history
        # We pass a copy of the history
        self.worker = AgentWorker(self.agent_executor, list(self.chat_history))
        self.worker.finished.connect(self.handle_response)
        self.worker.error.connect(self.handle_error)
        self.worker.start()

    def append_message(self, sender, text):
        color = "#3D8EC9" if sender == "You" else "#DDDDDD"
        self.result_area.append(f"<div style='margin-bottom: 10px;'><b style='color: {color};'>{sender}:</b><br>{text}</div>")
        # Scroll to bottom
        cursor = self.result_area.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.result_area.setTextCursor(cursor)

    @pyqtSlot(str)
    def handle_response(self, response):
        self.search_input.setDisabled(False)
        self.status_label.hide()
        self.append_message("Agent", response)
        self.chat_history.append(("ai", response))
        self.search_input.setFocus()

    @pyqtSlot(str)
    def handle_error(self, error_msg):
        self.search_input.setDisabled(False)
        self.status_label.setText("Error occurred.")
        self.append_message("System", f"Error: {error_msg}")
        self.search_input.setFocus()
    
    def keyPressEvent(self, event):
        # Close on Escape
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            event.accept()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def show_window(self):
        self.show()
        self.activateWindow()
        self.search_input.setFocus()
        self.center()
