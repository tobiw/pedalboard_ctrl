from functools import partial
from tkinter import Tk, Label, Button


class UiManager:
    def __init__(self):
        self.reset()

    def reset(self):
        # logging.debug('Reseting UI')

        try:
            for item in list(self._buttons.values()) + list(self._labels.values()):
                item.grid_forget()
                del item
        except AttributeError:  # _buttons or_labels doesn't exists yet
            pass

        self._buttons = {}
        self._labels = {}

        self._cur_col = 0
        self._cur_row = 0

    def mainloop(self):
        raise NotImplementedError

    def add_button(self, name, text, cb):
        if name in self._buttons:
            raise KeyError('Button {} already exists'.format(name))

        if cb is None:
            raise ValueError('cb cannot be None')

        self._cur_row += 1

        if self._cur_row > 4:
            self._cur_col += 1
            self._cur_row = 1

    def add_label(self, name, text):
        if name in self._labels:
            raise KeyError('Label {} already exists'.format(name))

        self._cur_row += 1
        if self._cur_row > 4:
            self._cur_col += 1
            self._cur_row = 1

    def update_item(self, name, text):
        raise NotImplementedError


class TkUi(UiManager):
    def __init__(self, fullscreen, fontsize):
        super().__init__()
        self._fontsize = fontsize

        self._ui = Tk()
        self._ui.title('UI')

        self._button_factory = partial(Button, master=self._ui, font=('Arial', self._fontsize), fg='white', bg='black')
        self._label_factory = partial(Label, master=self._ui, font=('Arial', self._fontsize // 2), fg='black')

        if fullscreen:
            self._ui.overrideredirect(True)
            self._ui.geometry("{}x{}+0+0".format(self._ui.winfo_screenwidth(), self._ui.winfo_screenheight()))

    def mainloop(self):
        self._ui.mainloop()

    def add_button(self, name, text, cb):
        super().add_button(name, text, cb)
        # logging.debug('Tk: adding button at ({:d}, {:d})'.format(self._cur_col, self._cur_row - 1))
        self._buttons[name] = self._button_factory(text=text, command=cb)
        self._buttons[name].grid(column=self._cur_col, row=self._cur_row - 1)

    def add_label(self, name, text):
        super().add_label(name, text)
        self._labels[name] = self._label_factory(text=text)
        self._labels[name].grid(column=self._cur_col, row=self._cur_row - 1)

    def update_item(self, name, text):
        self._labels[name]['text'] = text
