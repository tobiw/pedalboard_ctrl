import subprocess
import threading
import time


class Looper:
    def __init__(self):
        self._thread = threading.Thread(target=self._run_sooperlooper)

    def _run_sooperlooper(self):
        cmd = 'sooperlooper --loopcount=1 --channels=1 --looptime=60 --load-midi-binding=/home/pi/sl_midi.slb'.split()
        subprocess.call(cmd)
        print('=== sooperlooper process has ended ===')

    def start(self):
        self._thread.start()
        time.sleep(3)

        # Connect jack ports
        subprocess.call(['jack_connect', 'system:capture_1', 'sooperlooper:loop0_in_1'])
        for i in range(1, 3):
            subprocess.call(['jack_connect', 'sooperlooper:common_out_{}'.format(i), 'system:playback_{}'.format(i)])

        time.sleep(3)
        subprocess.call(['aconnect', 'USBMIDI', 'sooperlooper'])

    def stop(self):
        subprocess.call(['killall', 'sooperlooper'])
        self._thread.join()
