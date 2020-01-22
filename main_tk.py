import sys
import time
from tkinter import Tk, Label, Button


def btn_clicked():
    sys.exit(0)


def main():
    win = Tk()
    win.title("UI")
    l = Label(win, text="Hello", font=("Arial Bold", 64))
    l.grid(column=0, row=0)
    b = Button(win, text="Btn", command=btn_clicked)
    b.grid(column=0, row=1)
    win.mainloop()


if __name__ == '__main__':
    main()
