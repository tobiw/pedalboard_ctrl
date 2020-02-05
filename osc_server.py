from threading import Thread
from pythonosc import dispatcher, osc_server


class OscServer:
    """
    Central receiver for OSC messages which can control the program itself or sooperlooper.
    - /preset i:<N>: loads a preset (switches loops, starts/stops looper, selects drum loops)
    - /loop i:<N>: toggles a loop
    - /sl/<cmd>: passed through to sooperlooper instance
    """
    def __init__(self, use_threading=True):
        self._use_threading = use_threading
        self._port = 5005
        self._dispatcher = dispatcher.Dispatcher()

        self.register_uri("/ping", self.cb_ping)
        self.register_uri("/quit", self.cb_quit)
        self.register_uri("/preset/*", self.cb_preset)  # preset number (1-4)
        self.register_uri("/sl/*", self.cb_looper)  # looper commands ("undo", "record", etc)
        self.register_uri("/metronome/*", self.cb_metronome)  # Send metronome commands (e.g. a tap (1) or tap tempo value (30-300))

    def cb_preset(self, *args):
        raise NotImplementedError

    def cb_looper(self, *args):
        raise NotImplementedError

    def cb_metronome(self, *args):
        raise NotImplementedError

    def register_uri(self, uri, func, *args):
        self._dispatcher.map(uri, func, *args)

    def cb_ping(self, *args):
        print("PING " + str(list(args)))

    def cb_quit(self, *args):
        print("QUIT " + str(list(args)))
        self.stop()

    def start(self):
        self._server = osc_server.ThreadingOSCUDPServer(('0.0.0.0', self._port), self._dispatcher)
        if self._use_threading:
            self._thread = Thread(target=self._server.serve_forever)
            self._thread.start()
        else:
            self._server.serve_forever()

    def stop(self):
        self._server.shutdown()
