'''
Created on Mar 25, 2014

@author: shawkins

A simple CAN tracer

NOTE: Files generated from this tracer will not be consumable by PEAK software (or likely, any software)
'''

import datetime
import tempfile
import threading
from Queue import PriorityQueue, Empty


class CANTracer(threading.Thread):

    message_count = 1
    start_time = None
    abort = False
    output_queue = None

    def __init__(self, output_filename):
        threading.Thread.__init__(self)
        if output_filename:
            self.filename = output_filename
        else:
            self.filename = tempfile.NamedTemporaryFile().name
        self.start_time = datetime.datetime.now()
        self.output_queue = PriorityQueue()

        # Header message shamelessly stolen and modified from an actual .trc file
        HEADER_MESSAGE = """;
;   Message Number
;   |         Time Offset (ms)
;   |         |        Type
;   |         |        |        ID (hex)
;   |         |        |        |     Data Length Code
;   |         |        |        |     |   Data Bytes (hex) ...
;   |         |        |        |     |   |
;---+--   ----+----  --+--  ----+---  +  -+ -- -- -- -- -- -- --
"""
        with open(self.filename, 'w') as trace_file:
            trace_file.write(HEADER_MESSAGE)
        self.start()

    def run(self):
        while not self.abort:
            try:
                output_string = self.output_queue.get(block=True, timeout=0.01)
            except Empty:
                continue
            with open(self.filename, 'a') as trace_file:
                trace_file.write(output_string)

    def write_can_message(self, message):
        '''
        This method takes a TPCanMsg object and logs it to a "trace" file
        '''
        number_string = str(self.message_count).rjust(5) + ")"
        time = (datetime.datetime.now() - self.start_time).total_seconds()
        time_string = format(time * 1000, '0.1f').rjust(9)
        transmission_type = "Tx"
        type_string = transmission_type.rjust(5)
        id_string = format(message.ID, '04x').upper().rjust(8)
        length = message.LEN
        data_string = ""
        self.message_count += 1
        for byte in message.DATA:
            data_string += format(byte, '02x').upper() + " "
        self.output_queue.put(" " + number_string + "   " + time_string + "  " + type_string + "  " + id_string +
                              "  " + str(length) + "  " + data_string + "\n", block=True, timeout=1)

    def read_can_message(self, message, transmission_type="Rx"):
        '''
        This method takes a TPCanMsg object and logs it to a "trace" file
        '''
        number_string = str(self.message_count).rjust(5) + ")"
        time = (datetime.datetime.now() - self.start_time).total_seconds()
        time_string = format(time * 1000, '0.1f').rjust(9)
        transmission_type = "Rx"
        type_string = transmission_type.rjust(5)
        id_string = format(message.ID, '04x').upper().rjust(8)
        length = message.LEN
        data_string = ""
        self.message_count += 1
        for byte in message.DATA:
            data_string += format(byte, '02x').upper() + " "
        self.output_queue.put(" " + number_string + "   " + time_string + "  " + type_string + "  " + id_string +
                              "  " + str(length) + "  " + data_string + "\n", block=True, timeout=1)
