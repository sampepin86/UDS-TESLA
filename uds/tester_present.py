"""
Created on Mar 31, 2016

@author: jpetrie

@description: TesterPresent is a thread class to send tester present messages as a background process. See UDS.Basic for
    more detail on udsBasicRef, a necessary component.
"""

# Base Python
import time
import threading


class TesterPresent(threading.Thread):
    """
    Tester Present thread.  Sends Tester Present messages as a background process.
    """

    def __init__(self, uds_client_ref, interval=0.01, iterations=0):
        """
        Constructor
        :param uds_client_ref: <Client> a reference to the uds Basic handler.
        :param interval: <number> the period (1/freq) to send Tester Present messages.
        :param iterations: <number> the number of times to send the message. Default=0 (continuously)
        """
        self._abort = False
        self._sendTP = False
        self._uds = uds_client_ref
        self._interval = interval
        self._iterations = abs(iterations)
        self._lock = threading.Lock()  # Lock for the sendTP member.

        super(TesterPresent, self).__init__()

    def __enter__(self):
        """
        Easy Entrance
        """
        if self._iterations == 0:
            self.send()  # TODO: consider just changing it to 0...

    def __exit__(self, exception_type, exception_value, traceback):
        """
        Easy Exit
        """
        self.pause()

    def __del__(self):
        """
        Deconstructor
        """
        self.stop()  # TODO: test this

    def get_lock(self):
        """
        Get Lock returns our lock instance so it can be shared.
        :return lock: <threading.lock> our lock.
        """
        return self._lock

    def get_interval(self):
        """
        Get Interval gives access to the protected interval
        :return interval: <number> the time in seconds between tester present messages
        """
        with self._lock:
            return self._interval

    def set_interval(self, interval):
        """
        Set Interval sets the protected interval
        """
        with self._lock:
            self._interval = interval

    def send(self):
        """
        Send tells the thread to send Tester Present messages.
        """
        with self._lock:
            self._sendTP = True

    def pause(self):
        """
        Pause stops the thread from sending tester present messages in a way that can be resumed.
        """
        with self._lock:
            self._sendTP = False

    def stop(self):
        """
        Stop halts the thread and joins it.  The instance is depleted.
        """
        self.pause()
        self._abort = True
        self.join()

    def run(self):
        """
        Main worker thread.  Called by threading.Thread.start()  Sends tester present messages.
        """
        while not self._abort:
            with self._lock:
                if self._sendTP:
                    if self._iterations:
                        for _ in xrange(0, self._iterations):
                            time.sleep(self._interval)
                            self._uds.tester_present(False)
                        self._sendTP = False
                    else:
                        if self._sendTP:
                            time.sleep(self._interval)
                            self._uds.tester_present(False)


if __name__ == '__main__':
    # Do cool stuff
    print __doc__
    print TesterPresent.__doc__
