import logging
import subprocess
import threading
import time
from pythonosc import dispatcher, osc_server, udp_client


class LooperOscServer:
    """OSC server for receiving responses and updates from sooperlooper"""

    def __init__(self):
        self._log = logging.getLogger(__name__ + ':LooperOscServer')
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
        self._log.info('LooperOscServer started on port {}'.format(self._port))
        # TODO: register updates with sooperlooper

    def _osc_cb(self, *args):
        self._log.info("LooperOscServer._osc_cb: " + str(args))

    @property
    def uri(self):
        return 'osc.udp://localhost:{}'.format(self._port)


class SooperlooperOscInterface:
    """OSC client to communicate with sooperlooper"""
    def __init__(self, port):
        self._osc_client = udp_client.SimpleUDPClient('127.0.0.1', port)

        # OSC server for receiving responses and updates from sooperlooper
        self._osc_server = LooperOscServer()

        # Start OSC server and register for updates from sooperlooper
        self._osc_server.start()

    def register_update(self, loop, ctrl, return_path, auto_update=False):
        """/sl/0/register_update or /register_update, or ...register_auto_update"""
        prefix = ''
        if loop is not None or loop == -1:
            prefix += '/sl/{}'.format(loop)

        update_method = 'auto_update' if auto_update else 'update'

        self._osc_client.send_message(prefix + '/register_' + update_method, [ctrl, self._osc_server.uri, '/get_response'])

    def get(self, loop, ctrl):
        """/sl/0/get (e.g. 'state') or /get (e.g. 'tempo')"""
        prefix = ''
        if loop is not None or loop == -1:
            prefix += '/sl/{}'.format(loop)
        self._osc_client.send_message(prefix + '/get', [ctrl, self._osc_server.uri, '/get_response'])


class Looper:
    def __init__(self):
        # Config options for sooperlooper
        self._log = logging.getLogger(__name__ + ':Looper')
        self._sl_config = {
            'osc_port': 9951,
            'loops': 1,
            'channels': 1,
            'looptime': 60,
            'midi': 'sl_midi.slb'
        }

        # Thread to run sooperlooper in the background
        self._sl_thread = threading.Thread(target=self._run_sooperlooper)

        # OSC interface to send commands to sooperlooper
        self._sooperlooper_osc = SooperlooperOscInterface(self._sl_config['osc_port'])
        self._sooperlooper_osc.get(0, 'state')

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
        self._log.info('=== sooperlooper process has ended ===')

    @property
    def is_running(self):
        try:
            output = subprocess.check_output(['pgrep', 'sooperlooper'])
        except subprocess.CalledProcessError:
            # pgrep returned rc != 0 which means no process was found
            return False
        else:
            return output != ''

    def start(self):
        self._sl_thread.start()
        time.sleep(3)

        # Connect jack ports
        subprocess.call(['jack_connect', 'system:capture_1', 'sooperlooper:loop0_in_1'])
        for i in range(1, 3):
            # Mono output to all available sound card outputs
            subprocess.call(['jack_connect', 'sooperlooper:common_out_1'.format(i), 'system:playback_{}'.format(i)])

        time.sleep(3)

        # TODO: keep attempting to connect (so that it works if plugged in later)
        subprocess.call(['aconnect', 'USBMIDI', 'sooperlooper'])

        self._log.info('sooperlooper successfully started')

    def stop(self):
        subprocess.call(['killall', 'sooperlooper'])
        self._sl_thread.join()

    def state(self):
        state = 'Playing'
        return state
