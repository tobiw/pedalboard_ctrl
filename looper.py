import subprocess
import threading
import time
from pythonosc import dispatcher, osc_server, udp_client


class LooperOscServer:
    """OSC server for receiving responses and updates from sooperlooper"""

    def __init__(self):
        self._dispatcher = dispatcher.Dispatcher()
        for osc_uri in ['/quit', '/ping_response', '/get_response']:
            self._dispatcher.map(osc_uri, self._osc_cb)
        self._port = 9959
        self._server = osc_server.ThreadingOSCUDPServer(('0.0.0.0', self._port), self._dispatcher)
        self._thread = threading.Thread(target=self._run_server)

    def _run_server(self):
        self._thread = threading.Thread(target=self._server.serve_forever)

    def start(self):
        self._thread.start()
        print('LooperOscServer started on port {}'.format(self._port))
        # TODO: register updates with sooperlooper

    def _osc_cb(self, *args):
        print("LooperOscServer._osc_cb: " + str(args))


class Looper:
    def __init__(self):
        # Config options for sooperlooper
        self._sl_config = {
            'osc_port': 9951,
            'loops': 1,
            'channels': 1,
            'looptime': 60,
            'midi': '/home/pi/sl_midi.slb'
        }

        # Thread to run sooperlooper in the background
        self._sl_thread = threading.Thread(target=self._run_sooperlooper)

        # OSC client to send commands to sooperlooper
        self._osc_client = udp_client.SimpleUDPClient('127.0.0.1', self._sl_config['osc_port'])

        # OSC server for receiving responses and updates from sooperlooper
        self._osc_server = LooperOscServer()

    def _run_sooperlooper(self):
        cmd = [
            'sooperlooper',
            '--osc-port={}'.format(self._sl_config['osc_port']),
            '--loopcount={}'.format(self._sl_config['loops']),
            '--channels={}'.format(self._sl_config['channels']),
            '--looptime={}'.format(self._sl_config['looptime']),
            '--load-midi-binding={}'.format(self._sl_config['midi'])
        ]
        subprocess.call(cmd)
        print('=== sooperlooper process has ended ===')

    def start(self):
        self._sl_thread.start()
        time.sleep(3)

        # Connect jack ports
        subprocess.call(['jack_connect', 'system:capture_1', 'sooperlooper:loop0_in_1'])
        for i in range(1, 3):
            subprocess.call(['jack_connect', 'sooperlooper:common_out_{}'.format(i), 'system:playback_{}'.format(i)])

        time.sleep(3)

        # Start OSC server and register for updates from sooperlooper
        self._osc_server.start()

        # TODO: keep attempting to connect (so that it works if plugged in later)
        subprocess.call(['aconnect', 'USBMIDI', 'sooperlooper'])

    def stop(self):
        subprocess.call(['killall', 'sooperlooper'])
        self._sl_thread.join()

    def state(self):
        state = 'Playing'
        return state
