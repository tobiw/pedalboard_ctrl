import logging


class Menu:
    """
    A menu consists of buttons that can open other menus or
    trigger actions such as running a process.
    """
    ui = None

    def __init__(self, title, parent=None, auto_entry=True):
        self._log = logging.getLogger(__name__)
        self._title = title
        self._parent = parent
        self._ui_items = {}  # Tk/Wx independent

        # Add entry into main menu and back entry in this instance
        if parent and auto_entry:
            parent.add_item(title, title.capitalize(), lambda: parent.goto(self))
            self.add_item('back', 'Back', lambda: self.goto(parent))

    def __str__(self):
        return self._title

    def add_item(self, name, text, cb=None):
        self._ui_items[name] = (text, cb)

    def update_item(self, name, text):
        self.ui.update_item(name, text)

    def goto(self, obj):
        """Reconstructs the UI with the elements from the given menu object"""
        self._log.info('switching to {!s}'.format(obj))
        obj.make_ui()

    def make_ui(self):
        self.ui.reset()
        for name, item in self._ui_items.items():
            if name.startswith('lbl_'):
                self.ui.add_label(name, item[0])
            else:
                self.ui.add_button(name, item[0], item[1], last=name == 'back')
