import sys
import os
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow
from utils.hotkey import HotkeyListener
from utils.signal_bridge import HotkeyBridge
from agent.core import initialize_agent

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Initialize Agent
    print("Initializing Agent... (this may take a moment)")
    executor = initialize_agent()
    print("Agent Initialized.")

    # Initialize Main Window
    window = MainWindow(executor)

    # Bridge for thread-safe communication
    bridge = HotkeyBridge()

    def toggle_window():
        if window.isVisible():
            window.hide()
        else:
            window.show_window()
            
    # Connect signal to slot (this ensures toggle_window runs on main thread)
    bridge.request_toggle.connect(toggle_window)

    # Initialize Hotkey
    # The listener calls bridge.trigger(), which emits the signal.
    # Signals emitted from other threads are queued to the main thread.
    hotkey = HotkeyListener(bridge.trigger)
    hotkey.start()

    # System Tray
    tray = QSystemTrayIcon()
    tray.setIcon(QIcon.fromTheme("system-search")) # Or a default icon, or load one
    tray.setVisible(True)
    
    menu = QMenu()
    quit_action = menu.addAction("Quit")
    quit_action.triggered.connect(app.quit)
    tray.setContextMenu(menu)
    
    print("App Running. Press Ctrl+Alt+Space to toggle.")

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
