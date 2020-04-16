import logging
from rtmidi import RtMidiIn, RtMidiOut


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
        ch = msg.getChannel()
        cc = msg.getControllerNumber()

        self._log.debug('Received MIDI message: {} {}'.format(ch, cc))

        # TODO: map (ch, cc, value) to event
        if ch == 2:
            if cc == 117:
                # event-type (0:MIDI input), target(0:presets), cc
                self._app.send_event(0, 0, 117)
