import logging
import subprocess
import sys
from functools import partial
from menu import Menu
from ui_tk import TkUi


logging.basicConfig(level=logging.DEBUG)  #, format='%(asctime) - %(level) - %(message)')


def quit():
    logging.info('Exiting')
    sys.exit(0)


class MidiExpanderHandler:
    def __init__(self, ui):
        self._program = 'midisend'
        self._loop_state = [False] * 4
        for i in range(1, 5):
            ui.add_item('loop{}'.format(i), 'Loop {}'.format(i), partial(self._cb_loop, i))

    def get_midi_port_index(self):
        """Search for CH341"""
        output = subprocess.check_output([self._program, '--list']).decode()
        for line in output.splitlines():
            if 'aseqdump' in line:
                return int(line[0])
        return -1

    def _cb_loop(self, i):
        cmd = [
            self._program,  # midisend
            str(self.get_midi_port_index()),  # port
            '0',  # mode (0 = CC)
            str(80 - 1 + i),  # CC number (looper expects 80-83)
            '1' if self._loop_state[i - 1] else '0'
        ]
        logging.info(' '.join(cmd))
        subprocess.call(cmd)
        self._loop_state[i - 1] = not self._loop_state[i - 1]


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
