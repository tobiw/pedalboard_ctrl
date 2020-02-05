import logging
import subprocess
import sys
from functools import partial

from drum_sequencer import DrumSequencer
from looper import Looper
from menu import Menu
from osc_server import OscServer
from recorder import Recorder
from ui_tk import TkUi


logging.basicConfig(level=logging.DEBUG)  #, format='%(asctime) - %(level) - %(message)')


osc = OscServer()
looper = Looper()
recorder = Recorder()
drum_sequencer = DrumSequencer()


def quit():
    logging.info('Exiting')
    looper.stop()
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


class LooperHandler:
    def __init__(self, ui):
        self._ui = ui
        self._program = 'sendosc'
        self._recording = False
        ui.add_item('lbl_state', 'Loop state')
        for item in ['record', 'overdub', 'undo', 'redo', 'mute', 'trigger']:
            ui.add_item(item, item.capitalize(), partial(self._send_osc, item))

    def _send_osc(self, s):
        cmd = [self._program, '127.0.0.1', '9951', '/sl/0/hit', 's', s]
        logging.info(' '.join(cmd))
        subprocess.call(cmd)

        if s == 'record':
            self._recording = not self._recording
            logging.info('Recording: {!s}'.format(self._recording))
            self._ui.update_item('lbl_state', '{}recording'.format('' if self._recording else 'not '))


class RecordHandler:
    def __init__(self, ui):
        ui.add_item('record', 'Record', self.record_song)
        ui.add_item('stop', 'Stop', self.stop_recording)
        ui.add_item('delete', 'Delete', self.delete_last)

    def record_song(self):
        self._last_filename = recorder.filename
        recorder.start()

    def stop_recording(self):
        recorder.stop()

    def delete_last(self):
        subprocess.call(['rm', self._last_filename])


class DrumsHandler:
    def __init__(self, ui):
        ui.add_item('play', 'Play', self.play_song)
        ui.add_item('stop', 'Stop', self.stop_song)

    def play_song(self):
        drum_sequencer.start()

    def stop_song(self):
        drum_sequencer.stop()


def check_processes(list_of_processes):
    lines = subprocess.check_output(['ps', 'aux']).decode().splitlines()
    procs = [l.split()[10] for l in lines]
    return all(p in procs for p in list_of_processes)


def check_sound_card(expected_dev):
    output = subprocess.check_output(['aplay', '-l']).decode()
    return expected_dev in output


def check_midi(list_of_midi_devs):
    lines = subprocess.check_output(['aconnect', '-i', '-o']).decode().splitlines()
    clients = [l for l in lines if l.startswith('client')]
    for m in list_of_midi_devs:
        if not any(m in c for c in clients):
            return False
    return True


def main():
    # System checks
    assert check_sound_card('card 0:'), 'No ALSA device found'
    #assert check_sound_card('card 1:'), 'USB DAC not found'
    assert check_processes(['/usr/bin/jackd']), 'jackd must be running'
    assert check_midi(['System', 'Midi Through']), 'No MIDI devices found'
    #assert check_midi(['USBMIDI']), 'USB foot controller not found'

    Menu.ui = TkUi(fullscreen=True, fontsize=64)

    looper.start()

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
    midi_handler = LooperHandler(submenus['looper'])

    # Create recorder sub-menu
    record_handler = RecordHandler(submenus['record'])

    # Create drums sub-menu
    drums_handler = DrumsHandler(submenus['drums'])

    main_menu.make_ui()
    Menu.ui.mainloop()


if __name__ == '__main__':
    main()
