from rtmidi import RtMidiIn, RtMidiOut


class MidiReceiver:
    def __init__(self):
        self._midi_in, self._midi_out = RtMidiIn(), RtMidiOut()
        self._connect_midi('USBMIDI')
        self._midi_in.setCallback(self._midi_message_cb)

    def _connect_midi(self, midi_controller):
        def find_port(ports, name):
            for i, p in enumerate(ports):
                if p.startswith(name):
                    return i
            return None

        # Find the MIDI In port the Arduino Micro is connected to
        arduino_port = find_port([self._midi_in.getPortName(i) for i in range(self._midi_in.getPortCount())], midi_controller)
        if arduino_port is None:
            raise ValueError('Could not find "Arduino Micro" MIDI port')

        print("MidiIn connecting to {}".format(arduino_port))
        self._midi_in.openPort(arduino_port)

        # Find the MIDI Out port the Arduino Micro is connected to
        arduino_port = find_port([self._midi_out.getPortName(i) for i in range(self._midi_out.getPortCount())], midi_controller)
        assert arduino_port is not None
        print("MidiOut connecting to {}".format(arduino_port))
        self._midi_out.openPort(arduino_port)

    def _midi_message_cb(self, msg):
        print('MIDI CB: %s' % msg)


m = MidiReceiver()
while True:
    pass
