import logging
import subprocess
import sys
from functools import partial

import utility
from drum_sequencer import DrumSequencer
from looper import Looper
from menu import Menu
from osc_server import OscServer
from recorder import Recorder
from ui_tk import TkUi


logging.basicConfig(level=logging.DEBUG)  # , format='%(asctime) - %(level) - %(message)')


osc = OscServer()
looper = Looper()
recorder = Recorder()
drum_sequencer = DrumSequencer()


def quit():
    logging.info('Exiting')
    looper.stop()
    sys.exit(0)


class _MidiHandlerFunctionality:
    def __init__(self, ui):
        self._program = 'midisend'
        self._port_index = self.get_midi_port_index()

    def get_midi_port_index(self):
        """Search for CH345"""
        output = subprocess.check_output([self._program, '--list']).decode()
        for line in output.splitlines():
            if 'CH345' in line:
                return int(line[0])
        return -1


class MidiExpanderHandler(_MidiHandlerFunctionality):
    """
    Handle events in MIDI menu.

    Uses midisend external program to send MIDI CCs.
    """
    def __init__(self, ui):
        super().__init__(ui)

        self._loop_state = [False] * 4
        for i in range(1, 5):
            ui.add_item('loop{}'.format(i), 'Loop {}'.format(i), partial(self._cb_loop, i))

    def _cb_loop(self, i):
        cmd = [
            self._program,  # midisend
            str(self._port_index),  # port
            '0',  # mode (0 = CC)
            str(80 - 1 + i),  # CC number (looper expects 80-83)
            '1' if self._loop_state[i - 1] else '0'
        ]
        logging.info(' '.join(cmd))
        subprocess.call(cmd)
        self._loop_state[i - 1] = not self._loop_state[i - 1]


class PresetsHandler(_MidiHandlerFunctionality):
    """
    Handle events in Presets menu.

    Uses midisend external program to send MIDI CCs (similar to MidiExpanderHandler)
    """
    def __init__(self, ui):
        super().__init__(ui)

        self._current_preset = 0

        ui.add_item('off', 'Off', partial(self._cb_preset, 0))
        for i in range(1, 5):
            ui.add_item('preset{}'.format(i), 'Preset {}'.format(i), partial(self._cb_preset, i))

        self._presets = [
            [0, 0, 0, 0],
            [1, 0, 0, 0],
            [1, 1, 1, 1],
            [1, 0, 1, 0],
            [0, 0, 1, 1],
        ]

    def _cb_preset(self, i):
        self._current_preset = i
        for i, loop in enumerate(self._presets[self._current_preset]):
            cmd = [
                self._program,  # midisend
                str(self._port_index),  # port
                '0',  # mode (0 = CC)
                str(80 + i),  # CC number (looper expects 80-83)
                str(loop)
            ]
            logging.info(' '.join(cmd))
            subprocess.call(cmd)


class LooperHandler:
    """
    Handle events in Looper menu.

    Sends OSC commands to sooperlooper.
    """
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
    """
    Handle events in Record menu.

    Records the input via the Recorder class.
    """
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
    """
    Handle events in Drums menu.

    Plays back drum and backing tracks.
    """
    def __init__(self, ui):
        ui.add_item('play', 'Play', self.play_song)
        ui.add_item('stop', 'Stop', self.stop_song)

    def play_song(self):
        drum_sequencer.start()

    def stop_song(self):
        drum_sequencer.stop()


class UtilitiesHandler:
    """
    Handle events in Utilities menu.

    Various settings and utilities like setting up audio or MIDI connections.
    """
    def __init__(self, ui):
        self._ui = ui
        ui.add_item('midi-passthru', 'USBMIDI-CH345', self.midi_passthru)
        ui.add_item('flush-midi', 'Disconnect', self.flush_midi)
        ui.add_item('show-mapping', 'Mapping', self.show_midi_mapping)
        self._ui.add_item('lbl_mapping', 'n/a')

    def midi_passthru(self):
        logging.debug(subprocess.check_output(['aconnect', '-i', '-o']))
        logging.debug(subprocess.check_output(['aconnect', '-l']))
        assert utility.check_midi(['USBMIDI', 'CH345']), 'USBMIDI or CH345 adapter missing'
        subprocess.check_call(['aconnect', 'USBMIDI', 'CH345'])
        logging.info('Connected USBMIDI:0 to CH345:0')

    def flush_midi(self):
        logging.debug(subprocess.check_output(['aconnect', '-l']))
        subprocess.check_call(['aconnect', '-x'])

    def show_midi_mapping(self):
        mapping = '\n'.join(['test1', 'test2', 'test3'])
        logging.info(mapping)
        self._ui.update_item('lbl_mapping', mapping)


def main():
    # System checks
    assert utility.check_sound_card('card 0:'), 'No ALSA device found'
    # assert check_sound_card('card 1:'), 'USB DAC not found'
    assert utility.check_processes(['jackd']), 'jackd must be running'
    assert utility.check_midi(['System', 'Midi Through']), 'No MIDI devices found'
    # assert check_midi(['USBMIDI']), 'USB foot controller not found'

    Menu.ui = TkUi(fullscreen=True, fontsize=56)

    looper.start()

    main_menu = Menu('main')
    submenus = {name: Menu(name, main_menu) for name in ['midi', 'presets', 'looper', 'record', 'drums', 'utilities']}

    # Create main menu
    main_menu.add_item('quit', 'Quit', lambda: quit())

    # Create MIDI switcher sub-menu
    MidiExpanderHandler(submenus['midi'])

    # Create presets sub-menu
    PresetsHandler(submenus['presets'])

    # Create looper sub-menu
    LooperHandler(submenus['looper'])

    # Create recorder sub-menu
    RecordHandler(submenus['record'])

    # Create drums sub-menu
    DrumsHandler(submenus['drums'])

    # Create utilities sub-menu
    UtilitiesHandler(submenus['utilities'])

    main_menu.make_ui()
    Menu.ui.mainloop()


if __name__ == '__main__':
    main()
