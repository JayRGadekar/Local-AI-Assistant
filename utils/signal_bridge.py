from PyQt6.QtCore import QObject, pyqtSignal

class HotkeyBridge(QObject):
    """
    Bridge to send signals from non-GUI threads (pynput) to the GUI thread.
    """
    request_toggle = pyqtSignal()

    def trigger(self):
        self.request_toggle.emit()
