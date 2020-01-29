from tkinter import Tk, Label, Button


class UiManager:
    def __init__(self):
        self._buttons = {}
        self.reset()

    def reset(self):
        #logging.debug('Reseting UI')

        for b in self._buttons.values():
            b.grid_forget()
            del b

        self._buttons = {}

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


class TkUi(UiManager):
    def __init__(self, fullscreen, fontsize):
        super().__init__()
        self._fontsize = fontsize

        self._ui = Tk()
        self._ui.title('UI')

        if fullscreen:
            self._ui.overrideredirect(True)
            self._ui.geometry("{}x{}+0+0".format(self._ui.winfo_screenwidth(), self._ui.winfo_screenheight()))

    def mainloop(self):
        self._ui.mainloop()

    def add_button(self, name, text, cb):
        super().add_button(name, text, cb)
        #logging.debug('Tk: adding button at ({:d}, {:d})'.format(self._cur_col, self._cur_row - 1))
        self._buttons[name] = Button(self._ui, text=text, command=cb,
            font=('Arial', self._fontsize),
            fg='white', bg='black')
        self._buttons[name].grid(column=self._cur_col, row=self._cur_row - 1)


