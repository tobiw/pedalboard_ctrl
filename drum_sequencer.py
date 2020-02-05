import logging
import subprocess
import threading


class DrumSequencer:
    def __init__(self):
        self._log = logging.getLogger(__name__)
        self.current_filename = '/home/pi/GnR-Paradise_City.wav'
        self.running = False

    def _run_player(self):
        subprocess.call(['mplayer', '-ao', 'jack', self.current_filename])

    def start(self):
        self._thread = threading.Thread(target=self._run_player)
        self.running = True
        self._thread.start()
        self._log.info('drum sequencer thread has finished')
        self.running = False

    def stop(self):
        subprocess.call(['killall', 'mplayer'])
        self._thread.join()
