from tkinter import Tk, Label, Button


#l = Label(win, text="Hello", font=("Arial Bold", 64))
#l.grid(column=0, row=0)


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

    def generic_button_handler(self):
        print('Button pressed')

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
    def __init__(self):
        super().__init__()
        self._ui = Tk()
        self._ui.title('UI')

    def mainloop(self):
        self._ui.mainloop()

    def add_button(self, name, text, cb):
        super().add_button(name, text, cb)
        #logging.debug('Tk: adding button at ({:d}, {:d})'.format(self._cur_col, self._cur_row - 1))
        self._buttons[name] = Button(self._ui, text=text, font=('Arial', 48), command=cb)
        self._buttons[name].grid(column=self._cur_col, row=self._cur_row - 1)


