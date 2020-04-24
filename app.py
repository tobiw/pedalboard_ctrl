import argparse
import logging
import sys

import utility
from drum_sequencer import DrumSequencer
from ipc import IpcServer
from looper import Looper
from menu import Menu
from menu_handlers import BaseMenuHandler, MidiExpanderHandler, PresetsHandler, LooperHandler, RecordHandler, DrumsHandler, UtilitiesHandler, SystemHandler
from midi_receiver import MidiReceiver, MidiMapping
from osc_server import OscServer
from recorder import Recorder
from ui_tk import TkUi


class App:
    def __init__(self):
        self.ipc = IpcServer()  # Start IPC to webserver (server-side): mandatory but there might not be a client connecting to it
        self.osc = OscServer()  # Start app OSC server: mandatory but there might not be a client connecting to it
        self.looper = Looper()  # Start sooperlooper: optional (disable with --no-looper)
        self.recorder = Recorder()  # Init audio recorder: always on but no background activity
        self.drum_sequencer = DrumSequencer()  # Init audio/drums player: always on but no background activity

        # Only start MIDI receiver thread if USBMIDI device (foot pedal) is connected
        self.midi_receiver = MidiReceiver('USBMIDI', self) if utility.check_midi(['USBMIDI']) else None

        self._handlers = {}

    def quit(self):
        logging.info('Exiting')

        if self.looper and self.looper.is_running:
            self.looper.stop()

        self.ipc.stop()

        sys.exit(0)

    def send_event(self, event_target, event_payload):
        logging.debug('Event: {} {}'.format(event_target, event_payload))
        if event_target == MidiMapping.EVENT_TARGET_PRESET:
            self._handlers['presets'].trigger_preset(event_payload)
        elif event_target == MidiMapping.EVENT_TARGET_MIDI_LOOP:
            self._handlers['midi'].toggle(event_payload)
        elif event_target == MidiMapping.EVENT_TARGET_LOOPER:
            self._handlers['looper'].send_osc(event_payload)
        elif event_target == MidiMapping.EVENT_TARGET_DRUMS:
            self._handlers['drums'].play_song()

    def _parse_arguments(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-v', help='verbose', action='store_true', default=False)
        parser.add_argument('--no-looper', help='don\'t start looper', action='store_true', default=False)
        return parser.parse_args()

    def main(self):
        # Parse program arguments
        self.args = self._parse_arguments()
        logging.debug(self.args)

        # System checks
        assert utility.check_sound_card('card 0:'), 'No ALSA device found'
        # assert check_sound_card('card 1:'), 'USB DAC not found'
        # assert utility.check_processes(['jackd']), 'jackd must be running'
        assert utility.check_midi(['System', 'Midi Through']), 'No MIDI devices found'
        # assert check_midi(['USBMIDI']), 'USB foot controller not found'

        Menu.ui = TkUi(fullscreen=True, fontsize=56)

        self.ipc.start()

        if not self.args.no_looper:
            self.looper.start()

        main_menu = Menu('main')
        submenus = {name: Menu(name, main_menu) for name in ['midi', 'presets', 'looper', 'record', 'drums', 'utilities', 'system']}

        # Create main menu
        BaseMenuHandler.app = self
        self._handlers['midi'] = MidiExpanderHandler(submenus['midi'])
        self._handlers['presets'] = PresetsHandler(submenus['presets'])
        self._handlers['looper'] = LooperHandler(submenus['looper'])
        self._handlers['record'] = RecordHandler(submenus['record'])
        self._handlers['drums'] = DrumsHandler(submenus['drums'], self.drum_sequencer)
        self._handlers['utilities'] = UtilitiesHandler(submenus['utilities'])
        self._handlers['system'] = SystemHandler(submenus['system'])

        self._handlers['record'].recorder = self.recorder

        main_menu.make_ui()
        Menu.ui.mainloop()
