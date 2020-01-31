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
    submenus = { name: Menu(name, main_menu) for name in ['midi', 'presets', 'looper', 'record', 'drums']}

    # Create main menu
    main_menu.add_item('quit', 'Quit', lambda: quit())

    # Create MIDI switcher sub-menu
    midi_handler = MidiExpanderHandler(submenus['midi'])

    # Create presets sub-menu
    submenus['presets'].add_item('prev', 'Prev', lambda: logging.info('Going to previous preset'))
    submenus['presets'].add_item('next', 'Next', lambda: logging.info('Going to next preset'))

    # Create looper sub-menu
    submenus['looper'].add_item('record', 'Record', lambda: logging.info('SL record'))
    submenus['looper'].add_item('overdub', 'Overdub', lambda: logging.info('SL overdub'))
    submenus['looper'].add_item('undo', 'Undo', lambda: logging.info('SL undo'))

    # Create recorder sub-menu
    submenus['record'].add_item('record', 'Record', lambda: logging.info('Recording song ...'))
    submenus['record'].add_item('browse', 'Browse', lambda: logging.info('Browsing songs ...'))

    # Create drums sub-menu

    main_menu.make_ui()
    Menu.ui.mainloop()


if __name__ == '__main__':
    main()
