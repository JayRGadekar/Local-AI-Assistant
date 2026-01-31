from pynput import keyboard

class HotkeyListener:
    """
    Listens for a global hotkey (Ctrl+Alt+Space) to trigger a callback.
    """
    def __init__(self, on_trigger_callback):
        self.on_trigger_callback = on_trigger_callback
        self.listener = None

    def start(self):
        # Define the hotkey combination
        # <ctrl>+<alt>+<space>
        self.listener = keyboard.GlobalHotKeys({
            '<ctrl>+<alt>+<space>': self.on_activate
        })
        self.listener.start()

    def on_activate(self):
        if self.on_trigger_callback:
            self.on_trigger_callback()

    def stop(self):
        if self.listener:
            self.listener.stop()
