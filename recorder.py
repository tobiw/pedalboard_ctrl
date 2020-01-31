import subprocess
import threading


class Recorder:
    def __init__(self):
        self._thread = threading.Thread(target=self._run_recorder)
        self._current_file_index = 1

    @property
    def filename(self):
        return '/home/pi/recording{:04d}.wav'.format(self._current_file_index)

    def _run_recorder(self):
        cmd = 'jack_rec -f {} system:playback_1'.split()
        subprocess.call(['jack_rec', '-f', self.filename, 'sooperlooper:common_out_1'])

    def start(self):
        self._thread.start()
        print('=== recorder thread has finished ===')
        self._current_file_index += 1

    def stop(self):
        subprocess.call(['killall', 'jack_rec'])
        self._thread.join()
