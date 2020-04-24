import logging
from rtmidi import RtMidiIn, RtMidiOut


class MidiMapping:
    EVENT_TARGET_MIDI_LOOP = 0
    EVENT_TARGET_PRESET = 1
    EVENT_TARGET_LOOPER = 2
    EVENT_TARGET_RECORDER = 3
    EVENT_TARGET_DRUMS = 4

    def __init__(self, channel, cc, event_target, payload):
        if event_target not in [
            self.EVENT_TARGET_MIDI_LOOP,
            self.EVENT_TARGET_DRUMS,
            self.EVENT_TARGET_LOOPER,
            self.EVENT_TARGET_PRESET,
            self.EVENT_TARGET_RECORDER
        ]:
            raise ValueError('event_target must be one of MidiMapping.EVENT_TARGET_...')

        self.channel = channel
        self.cc = cc
        self.event_target = event_target
        self.payload = payload


class MidiReceiver:
    """
    Handles incoming MIDI messages from attached controllers or instruments.

    Incoming messages can be remapped to other MIDI events, OSC, or trigger
    events inside the app.
    """
    def __init__(self, usb_device_name, app):
        self._log = logging.getLogger(__name__)
        self._midi_in, self._midi_out = RtMidiIn(), RtMidiOut()
        self._connect_midi(usb_device_name)
        self._midi_in.setCallback(self._midi_message_cb)
        self._app = app
        self.enabled = True

    def _connect_midi(self, usb_device_name):
        def find_port(ports, name):
            for i, p in enumerate(ports):
                if p.startswith(name):
                    return i
            return None

        # Find the MIDI In port
        port = find_port([self._midi_in.getPortName(i) for i in range(self._midi_in.getPortCount())], usb_device_name)
        if port is None:
            raise ValueError('Could not find "{}" MIDI port'.format(usb_device_name))

        self._log.info("MidiIn connecting to {}".format(port))
        self._midi_in.openPort(port)

        # Find the MIDI Out port
        port = find_port([self._midi_out.getPortName(i) for i in range(self._midi_out.getPortCount())], usb_device_name)
        assert port is not None
        self._log.info("MidiOut connecting to {}".format(port))
        self._midi_out.openPort(port)

    def _midi_message_cb(self, msg):
        if not self.enabled:
            return

        ch = msg.getChannel()
        cc = msg.getControllerNumber()

        self._log.debug('Received MIDI message: {} {}'.format(ch, cc))

        # Mapping (channel, cc, value) to event
        self._mapping = [
            # single click
            MidiMapping(channel=2, cc=10, event_target=MidiMapping.EVENT_TARGET_MIDI_LOOP, payload=1),  # toggle loop 1
            # MidiMapping(channel=2, cc=11, event_target=MidiMapping.EVENT_TARGET_DRUMS, payload=1),  # play drums
            # MidiMapping(channel=2, cc=12, event_target=MidiMapping.EVENT_TARGET_LOOPER, payload='record'),  # record
            # MidiMapping(channel=2, cc=13, event_target=MidiMapping.EVENT_TARGET_LOOPER, payload='stop'),  # stop
            MidiMapping(channel=2, cc=14, event_target=MidiMapping.EVENT_TARGET_PRESET, payload=0),  # switch loops off
            MidiMapping(channel=2, cc=15, event_target=MidiMapping.EVENT_TARGET_PRESET, payload=1),  # switch to preset 1
            MidiMapping(channel=2, cc=16, event_target=MidiMapping.EVENT_TARGET_PRESET, payload=2),  # switch to preset 2
            MidiMapping(channel=2, cc=17, event_target=MidiMapping.EVENT_TARGET_PRESET, payload=3),  # switch to preset 3

            # long click
        ]

        def find_mapping(ch_, cc_):
            for m in self._mapping:
                if m.channel == ch_ and m.cc == cc_:
                    return m

        m = find_mapping(ch, cc)
        if m:
            self._log.info('Sending event {}:{}'.format(m.event_target, m.payload))
            self._app.send_event(m.event_target, m.payload)
