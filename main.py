import logging
import sys
from functools import partial
from menu import Menu
from ui_tk import TkUi


logging.basicConfig(level=logging.DEBUG)  #, format='%(asctime) - %(level) - %(message)')


def quit():
    logging.info('Exiting')
    sys.exit(0)


def loop1():
    logging.info('send MIDI: toggle loop 1')

def loop2():
    logging.info('send MIDI: toggle loop 2')

def loop3():
    logging.info('send MIDI: toggle loop 3')

def loop4():
    logging.info('send MIDI: toggle loop 4')


class MidiExpanderHandler:
    def __init__(self, ui):
        for i in range(1, 5):
            ui.add_item('loop{}'.format(i), 'Loop {}'.format(i), partial(self._cb_loop, i))

    def _cb_loop(self, i):
        logging.info('send MIDI: toggle loop {}'.format(i))


def main():
    Menu.ui = TkUi(fullscreen=True, fontsize=64)

    main_menu = Menu('main')
    midi_switcher_menu = Menu('midi', main_menu)
    looper_menu = Menu('looper', main_menu)

    # Create main menu
    main_menu.add_item('quit', 'Quit', lambda: quit())
    main_menu.add_item('midi', 'Midi', lambda: main_menu.goto(midi_switcher_menu))
    main_menu.add_item('looper', 'Looper', lambda: main_menu.goto(looper_menu))
    main_menu.make_ui()

    # Create MIDI switcher sub-menu
    midi_switcher_menu.add_item('back', 'Back', lambda: midi_switcher_menu.goto(main_menu))
    midi_handler = MidiExpanderHandler(midi_switcher_menu)

    # Create looper sub-menu
    # TODO: implement callbacks in separate module/class
    looper_menu.add_item('back', 'Back', lambda: looper_menu.goto(main_menu))
    looper_menu.add_item('record', 'Record', lambda: logging.info('SL record'))
    looper_menu.add_item('overdub', 'Overdub', lambda: logging.info('SL overdub'))
    looper_menu.add_item('undo', 'Undo', lambda: logging.info('SL undo'))

    Menu.ui.mainloop()


if __name__ == '__main__':
    main()
