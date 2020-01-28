class Menu:
    """
    A menu consists of buttons that can open other menus or
    trigger actions such as running a process.
    """
    ui = None

    def __init__(self, title, parent=None):
        self._title = title
        self._parent = parent
        self._buttons = {}  # Tk/Wx independent

    def __str__(self):
        return self._title

    def add_item(self, name, text, cb):
        self._buttons[name] = (text, cb)

    def goto(self, obj):
        """Reconstructs the UI with the elements from the given menu object"""
        #logging.info('switching to {!s}'.format(obj))
        obj.make_ui()

    def make_ui(self):
        self.ui.reset()
        for name, item in self._buttons.items():
            self.ui.add_button(name, item[0], item[1])
