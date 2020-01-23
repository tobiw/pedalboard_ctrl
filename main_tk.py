import sys
import time
from tkinter import Tk, Label, Button


#l = Label(win, text="Hello", font=("Arial Bold", 64))
#l.grid(column=0, row=0)

class UiManager:
    def __init__(self):
        self._buttons = {}
        self._cur_row = 0

    def mainloop(self):
        raise NotImplementedError

    def generic_button_handler(self):
        print('Button pressed')

    def add_button(self, name, text, cb=None):
        if name in self._buttons:
            raise KeyError('Button {} already exists'.format(name))

        self._cur_row += 1


class TkUi(UiManager):
    def __init__(self):
        super().__init__()
        self._ui = Tk()
        self._ui.title('UI')

    def mainloop(self):
        self._ui.mainloop()

    def add_button(self, name, text, cb=None):
        super().add_button(name, text, cb)

        if cb is None:
            cb = self.generic_button_handler

        self._buttons[name] = Button(self._ui, text=text, font=('Arial', 48), command=cb)
        self._buttons[name].grid(column=0, row=self._cur_row - 1)


def main():
    ui = TkUi()
    ui.add_button('quit', 'Quit', lambda: sys.exit(0))
    ui.add_button('one', 'One')
    ui.add_button('two', 'Two')
    ui.mainloop()


if __name__ == '__main__':
    main()
