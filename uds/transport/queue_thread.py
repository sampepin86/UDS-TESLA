"""
Created on Jul 28 2016
@author: trseroff

"""

# Base Python
import threading
import time
from collections import deque

# Constants
DEFAULT_READ_TIMEOUT_SECONDS = 3
POLLING_INTERVAL = .005  # In seconds.


class QueueThread(threading.Thread):
    """
    QueueThread provides read queues filtered by nodeID information.
    """

    def __init__(self, read_func, timeout=DEFAULT_READ_TIMEOUT_SECONDS):
        """
        Constructor
        :param read_func: reference to the read function for the transport layer
            Messages returned by read_func must have member 'ID' for filtering, but all other structure is flexible
        :param timeout: max time to try reading a message from a queue before timing out
        """

        # Threading stuff
        super(QueueThread, self).__init__()
        self.daemon = True
        self.running = True

        self._timeout = timeout

        self._read_func = read_func

        # At first, we won't have any read queues, since there aren't any nodes configured yet
        self.read_queues = {}
        # Each message ID / queue has a lock associated with it.
        self.locks = {}

    def add_read_queue(self, msg_id):
        """
        Add a read queue for the specified CAN message ID
        :param msg_id: The CAN message ID the new read queue will be for
        """
        new_queue = deque([])
        self.read_queues[msg_id] = new_queue
        self.locks[msg_id] = threading.Lock()

    def remove_read_queue(self, msg_id):
        """
        Remove the specified CAN message ID's read queue
        :param msg_id: The CAN message ID whose read queue we should delete
        """
        if msg_id in self.read_queues:
            del self.read_queues[msg_id]
        if msg_id in self.locks:
            del self.locks[msg_id]

    def set_read_timeout(self, timeout):
        """
        Set the message receive timeout
        :param timeout: <seconds> Value to use as new signal read timeout length
        """
        self._timeout = timeout

    def read(self, msg_id):
        """
        Read pops a message off of the Read Queue for the specified CAN message ID and returns it.
        :param msg_id: CAN message ID of the read queue to check
        :return: a Message, or None if there was nothing on the Queue
        """
        message = None
        starttime = time.time()
        if msg_id in self.read_queues:
            while time.time() - starttime < self._timeout:
                if len(self.read_queues[msg_id]) > 0:
                    with self.locks[msg_id]:
                        return self.read_queues[msg_id].popleft()
                time.sleep(POLLING_INTERVAL)

        return message

    def clear_queues(self, msg_id):
        """
        clear_queues allows the user to clear the read queue for the specified message ID
        :param msg_id: The CAN message ID of the read queue to clear
        """
        if msg_id in self.read_queues:
            with self.locks[msg_id]:
                self.read_queues[msg_id].clear()
                return True
        else:
            return False

    def run(self):
        """
        Main worker thread. Reads the hardware and stores relevant messages into the read queues. Called by start().
        """
        received_msg = None
        while self.running:
            received_msg = self._read_func()

            if received_msg is None:
                # Skip over failed reads.
                continue

            # If there's a read queue for the message ID, get the lock and add the message to the queue
            if received_msg.ID in self.read_queues:
                with self.locks[received_msg.ID]:
                    self.read_queues[received_msg.ID].append(received_msg)

            # Otherwise throw out the message
            received_msg = None
            time.sleep(POLLING_INTERVAL)

    def finish(self):
        """
        Shuts down the worker thread
        """
        self.running = False
        self.join()

if __name__ == "__main__":
    print __doc__
    print QueueThread.__doc__
