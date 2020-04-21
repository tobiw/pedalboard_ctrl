import logging
import subprocess
import utility

from functools import partial


class _MidiHandlerFunctionality:
    def __init__(self, ui):
        self._program = 'midisend'
        try:
            self._port_index = self.get_midi_port_index()
        except FileNotFoundError:
            self._port_index = None

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
        self._log = logging.getLogger('MidiExpanderHandler')
        super().__init__(ui)

        self._loop_state = [False] * 4
        for i in range(1, 5):
            ui.add_item('loop{}'.format(i), 'Loop {}'.format(i), partial(self.toggle, i))

    def toggle(self, i):
        cmd = [
            self._program,  # midisend
            str(self._port_index),  # port
            '0',  # mode (0 = CC)
            str(80 - 1 + i),  # CC number (looper expects 80-83)
            '1' if self._loop_state[i - 1] else '0'
        ]
        self._log.info(' '.join(cmd))
        subprocess.call(cmd)
        self._loop_state[i - 1] = not self._loop_state[i - 1]


class PresetsHandler(_MidiHandlerFunctionality):
    """
    Handle events in Presets menu.

    Uses midisend external program to send MIDI CCs (similar to MidiExpanderHandler)
    """
    def __init__(self, ui):
        self._log = logging.getLogger('PresetsHandler')
        super().__init__(ui)

        self._current_preset = 0

        preset_names = ['----', 'DynDrv', 'DynMod', 'Drv', 'Mod', 'all']
        for i, name in enumerate(preset_names):
            ui.add_item('preset{}'.format(i), name, partial(self.trigger_preset, i))

        # Loops: Overdrive, Modulation, n/a, Dynamics
        self._presets = [
            [0, 0, 0, 0],  # off
            [1, 0, 0, 1],  # DynDrv
            [0, 1, 0, 1],  # DynMod
            [1, 0, 0, 0],  # Drv
            [0, 1, 0, 0],  # Mod
            [1, 1, 0, 1],  # all (loop 3 not valid at the moment)
        ]

    def trigger_preset(self, i):
        self._current_preset = i
        for i, loop in enumerate(self._presets[self._current_preset]):
            cmd = [
                self._program,  # midisend
                str(self._port_index),  # port
                '0',  # mode (0 = CC)
                str(80 + i),  # CC number (looper expects 80-83)
                str(loop)
            ]
            self._log.info(' '.join(cmd))
            subprocess.call(cmd)


class LooperHandler:
    """
    Handle events in Looper menu.

    Sends OSC commands to sooperlooper.
    """
    def __init__(self, ui):
        self._log = logging.getLogger('LooperHandler')
        self._ui = ui
        self._program = 'sendosc'
        self._recording = False
        ui.add_item('lbl_state', 'Loop state')
        for item in ['record', 'overdub', 'undo', 'redo', 'mute', 'trigger']:
            ui.add_item(item, item.capitalize(), partial(self.send_osc, item))

    def send_osc(self, s):
        cmd = [self._program, '127.0.0.1', '9951', '/sl/0/hit', 's', s]
        self._log.info(' '.join(cmd))
        subprocess.call(cmd)

        if s == 'record':
            self._recording = not self._recording
            self._log.info('Recording: {!s}'.format(self._recording))
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
        self._last_filename = self.recorder.filename
        self.recorder.start()

    def stop_recording(self):
        self.recorder.stop()

    def delete_last(self):
        subprocess.call(['rm', self._last_filename])


class DrumsHandler:
    """
    Handle events in Drums menu.

    Plays back drum and backing tracks.
    """
    def __init__(self, ui, drum_sequencer):
        ui.add_item('stop', 'Stop', self.stop_song)
        for i, (title, _) in enumerate(drum_sequencer.songs):
            ui.add_item('play{}'.format(i), title, partial(self.play_song, i))

        self._drum_sequencer = drum_sequencer

    def play_song(self, i):
        self._drum_sequencer.selection = i
        self._drum_sequencer.start()

    def stop_song(self):
        self._drum_sequencer.stop()


class UtilitiesHandler:
    """
    Handle events in Utilities menu.

    Various settings and utilities like setting up audio or MIDI connections.
    """
    def __init__(self, ui):
        self._log = logging.getLogger('UtilitiesHandler')
        self._ui = ui
        ui.add_item('midi-passthru', 'Midi thru', self.midi_passthru)
        ui.add_item('audio-passthru', 'Audio thru', self.audio_passthru)
        ui.add_item('flush-midi', 'Disconnect', self.flush_midi)
        ui.add_item('show-mapping', 'Mapping', self.show_midi_mapping)
        ui.add_item('lbl_mapping', 'n/a')

    def midi_passthru(self):
        self._log.debug(subprocess.check_output(['aconnect', '-i', '-o']))
        self._log.debug(subprocess.check_output(['aconnect', '-l']))
        assert utility.check_midi(['USBMIDI', 'CH345']), 'USBMIDI or CH345 adapter missing'
        subprocess.check_call(['aconnect', 'USBMIDI', 'CH345'])
        self._log.info('Connected USBMIDI:0 to CH345:0')

    def audio_passthru(self):
        self._log.debug(subprocess.check_output(['jack_lsp', '-c']))
        subprocess.check_call(['jack_connect', 'system:capture_1', 'system:playback_1'])
        self._log.info('Connected system:capture to system:playback')

    def flush_midi(self):
        self._log.debug(subprocess.check_output(['aconnect', '-l']))
        subprocess.check_call(['aconnect', '-x'])

    def show_midi_mapping(self):
        mapping = '\n'.join(['test1', 'test2', 'test3'])
        self._log.info(mapping)
        self._ui.update_item('lbl_mapping', mapping)


class SystemHandler:
    """
    Handle events in System menu.

    Controlling services and the Raspberry Pi.
    """
    def __init__(self, ui):
        ui.add_item('exit', 'Exit', self.exit_app)
        ui.add_item('poweroff', 'Poweroff', self.poweroff_system)
        self.app = None

    def exit_app(self):
        self.app.quit()

    def poweroff_system(self):
        subprocess.call(['sudo', 'poweroff'])
