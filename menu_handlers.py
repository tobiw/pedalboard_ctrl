import logging
import rtmidi
import subprocess
import utility

from functools import partial


class BaseMenuHandler:
    app = None


class _MidiHandlerFunctionality(BaseMenuHandler):
    def __init__(self, ui):
        self._midi = {name: rtmidi.RtMidiOut() for name in ['looper', 'ctrl']}
        loop_port_index = self.get_midi_port_index(self._midi['looper'], 'CH345')
        ctrl_port_index = self.get_midi_port_index(self._midi['ctrl'], 'USBMIDI')
        self._midi['looper'].openPort(loop_port_index)
        self._midi['ctrl'].openPort(ctrl_port_index)
        assert self._midi['looper'].isPortOpen()
        assert self._midi['ctrl'].isPortOpen()

    def get_midi_port_index(self, midi_port, name):
        """Search for MIDI device"""
        for i, port_name in enumerate([midi_port.getPortName(i) for i in range(midi_port.getPortCount())]):
            if name in port_name:
                return i
        return -1

    def _send_cc(self, port_name, cc, value):
        self._log.debug('Sending CC ({}, {}, {}) to {}'.format(1, cc, value, port_name))
        msg = rtmidi.MidiMessage().controllerEvent(1, cc, value)
        self._midi[port_name].sendMessage(msg)


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
        self._loop_state[i - 1] = not self._loop_state[i - 1]
        self._send_cc('looper', 80 - 1 + i, int(self._loop_state[i - 1]))
        self._send_cc('ctrl', i, int(self._loop_state[i - 1]))


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

        for loop_i, loop in enumerate(self._presets[self._current_preset]):
            self._send_cc('looper', 80 + loop_i, loop)

        for clear_i in range(4):
            self._send_cc('ctrl', 5 + clear_i, 0)
        self._send_cc('ctrl', 5 + self._current_preset, 1)


class LooperHandler(BaseMenuHandler):
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
        self._log.debug(' '.join(cmd))
        subprocess.call(cmd)

        if s == 'record':
            self._recording = not self._recording
            self._log.info('Recording: {!s}'.format(self._recording))
            self._ui.update_item('lbl_state', '{}recording'.format('' if self._recording else 'not '))


class RecordHandler(BaseMenuHandler):
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


class DrumsHandler(BaseMenuHandler):
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


class UtilitiesHandler(BaseMenuHandler):
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
        self.app.midi_receiver.enable = False  # disable while passthru is active
        self._log.info('MidiReceiver disabled')

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


class SystemHandler(BaseMenuHandler):
    """
    Handle events in System menu.

    Controlling services and the Raspberry Pi.
    """
    def __init__(self, ui):
        ui.add_item('exit', 'Exit', self.exit_app)
        ui.add_item('poweroff', 'Poweroff', self.poweroff_system)

    def exit_app(self):
        self.app.quit()

    def poweroff_system(self):
        subprocess.call(['sudo', 'poweroff'])
