import logging
import os.path
import subprocess
import threading


class DrumSequencer:
    def __init__(self):
        self._log = logging.getLogger(__name__)
        self._path = '/home/pi'
        self.songs = [('Kick', 'kick-180bpm.wav'), ('GnR', 'GnR-Paradise_City.wav'), ('FF', 'FF-Pretender.wav')]
        self.selection = 0
        self.running = False

    def _run_player(self):
        subprocess.call(['mplayer', '-ao', 'jack', os.path.join(self._path, self.songs[self.selection][1])])

    def start(self):
        self._thread = threading.Thread(target=self._run_player)
        self.running = True
        self._thread.start()
        self._log.info('drum sequencer thread has finished')
        self.running = False

    def stop(self):
        subprocess.call(['killall', 'mplayer'])
        self._thread.join()
