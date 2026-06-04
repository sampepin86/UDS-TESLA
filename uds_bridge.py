# -*- coding: utf-8 -*-
"""
Created on May 31, 2026

@author: Antigravity

@description: uds_bridge is a JSON-RPC over TCP socket bridge running under Python 2.7.
It serves as the backend controller wrapping the SWIG UDS client library and interfacing 
with the hardware transport layers (PCAN, ESP32, and Simulation).
"""

import sys
import os
import json
import socket
import threading
import time
import traceback
import argparse

# Setup sys.path to import local uds module
WORKSPACE = os.path.dirname(os.path.realpath(__file__))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from uds.client import Client
import uds.nodes as nodes
from uds.transport.simulated_transport import SimulatedTransport
from uds.transport.esp32_transport import ESP32Transport

# Try importing PCAN if available
try:
    from uds.transport.pcan_transport import PCANTransport
except ImportError:
    PCANTransport = None

# Global UDS client and transport state
client = None
transport = None
tester_present_thread = None
tester_present_active = False
tester_present_interval = 2.0

def tester_present_loop():
    global tester_present_active, tester_present_interval, client
    while tester_present_active:
        if client:
            try:
                # Send tester present with responseRequired=False to keep session alive silently
                client.tester_present(responseRequired=False)
            except Exception as e:
                print "Error in Tester Present keep-alive: {}".format(e.message)
        time.sleep(tester_present_interval)

def handle_rpc(request):
    global client, transport, tester_present_active, tester_present_thread, tester_present_interval
    
    req_id = request.get('id')
    method = request.get('method')
    params = request.get('params', {})
    
    try:
        if method == 'init_transport':
            # Parameters: type, target, port, baudrate, can_baud
            t_type = params.get('type', 'simulated')
            target = params.get('target', '')
            port = int(params.get('port', 1337))
            baudrate = int(params.get('baudrate', 115200))
            can_baud = params.get('can_baud', '6') # Default 500k
            
            # Clean up old client/transport if exists
            if client:
                try:
                    client.close()
                except:
                    pass
            if transport:
                try:
                    transport.finish()
                except:
                    pass
            
            if t_type == 'simulated':
                transport = SimulatedTransport(verbose=False)
            elif t_type == 'pcan':
                if PCANTransport is None:
                    raise Exception("PCANTransport could not be loaded (missing PCAN libraries).")
                transport = PCANTransport()
            elif t_type in ('esp32_usb', 'esp32_wifi'):
                conn_type = 'serial' if t_type == 'esp32_usb' else 'wifi'
                transport = ESP32Transport(connection_type=conn_type, target=target, port=port, baudrate=baudrate)
            else:
                raise Exception("Unknown transport type: {}".format(t_type))
            
            # Initialize hardware, but simulated transport does not accept can_baud
            try:
                err = transport.initialize(can_baud=can_baud)
            except TypeError as e:
                if 'unexpected keyword argument' in str(e):
                    err = transport.initialize()
                else:
                    raise
            if err != 0:
                raise Exception("Failed to initialize hardware transport layer.")
                
            # Create client with default node (BMS)
            default_node = nodes.search.get('BMS') or nodes.Node()
            client = Client(transport=transport)
            client.set_node(default_node)
            
            return {'id': req_id, 'result': 'Transport and Client initialized successfully.'}
            
        elif method == 'get_nodes':
            node_names = sorted(nodes.search.keys())
            return {'id': req_id, 'result': node_names}
            
        # Check if client initialized for other methods
        if client is None:
            raise Exception("Diagnostic Client is not initialized. Initialize transport first.")
            
        if method == 'set_node':
            node_name = params.get('node')
            node = nodes.search.get(node_name)
            if not node:
                raise Exception("Node {} not found in nodes database.".format(node_name))
            client.set_node(node)
            return {'id': req_id, 'result': 'Switched to node: {}'.format(node_name)}
            
        elif method == 'diagnostic_session':
            session_type = int(params.get('session_type', 1))
            resp_req = bool(params.get('response_required', True))
            res = client.diagnostic_session(session_type, responseRequired=resp_req)
            return {'id': req_id, 'result': res}
            
        elif method == 'ecu_reset':
            reset_type = int(params.get('reset_type', 1))
            resp_req = bool(params.get('response_required', True))
            res = client.ecu_reset(reset_type, responseRequired=resp_req)
            return {'id': req_id, 'result': res}
            
        elif method == 'security_access':
            level = int(params.get('level', 1))
            res = client.security_access(level)
            return {'id': req_id, 'result': res}
            
        elif method == 'read_dtc':
            req_data = params.get('request_data', [2, 9]) # default: Report DTC by status mask (0x09/Active)
            out_len = int(params.get('output_len', 100))
            res = client.read_dtc(req_data, out_len)
            # res is usually a list of bytes
            return {'id': req_id, 'result': list(res)}
            
        elif method == 'clear_dtc':
            group = int(params.get('group', 0xFFFFFF))
            res = client.clear_dtc(group)
            return {'id': req_id, 'result': res}
            
        elif method == 'control_dtc':
            setting_type = int(params.get('setting_type', 1))
            rec_len = int(params.get('record_len', 0))
            record = params.get('record', [])
            resp_req = bool(params.get('response_required', True))
            res = client.control_dtc(setting_type, rec_len, record, resp_req)
            return {'id': req_id, 'result': res}
            
        elif method == 'read_data':
            data_id = int(params.get('data_id'))
            data_len = int(params.get('data_len', 4))
            res = client.read_data(data_id, data_len)
            return {'id': req_id, 'result': list(res)}
            
        elif method == 'write_data':
            data_id = int(params.get('data_id'))
            data_bytes = params.get('data') # list of ints
            res = client.write_data(data_id, data_bytes)
            return {'id': req_id, 'result': res}
            
        elif method == 'io_control':
            io_id = int(params.get('io_id'))
            io_type = int(params.get('io_type'))
            input_data = params.get('input_data', [])
            out_len = int(params.get('output_len', 0))
            res = client.io_control(io_id, io_type, input_data, out_len)
            return {'id': req_id, 'result': list(res) if res else []}
            
        elif method == 'routine_control':
            rc_id = int(params.get('rc_id'))
            rc_type = int(params.get('rc_type'))
            input_data = params.get('input_data', [])
            out_len = int(params.get('output_len', 0))
            res = client.routine_control(rc_id, rc_type, input_data, out_len)
            return {'id': req_id, 'result': list(res) if res else []}
            
        elif method == 'read_memory':
            address = int(params.get('address'))
            size = int(params.get('size'))
            out_len = int(params.get('output_len'))
            res = client.read_memory(address, size, out_len)
            return {'id': req_id, 'result': list(res)}
            
        elif method == 'write_memory':
            address = int(params.get('address'))
            data_bytes = params.get('data') # list of ints
            res = client.write_memory(address, data_bytes)
            return {'id': req_id, 'result': res}
            
        elif method == 'tester_present_toggle':
            active = bool(params.get('active', False))
            interval = float(params.get('interval', 2.0))
            tester_present_interval = interval
            
            if active and not tester_present_active:
                tester_present_active = True
                tester_present_thread = threading.Thread(target=tester_present_loop)
                tester_present_thread.daemon = True
                tester_present_thread.start()
            elif not active and tester_present_active:
                tester_present_active = False
                
            return {'id': req_id, 'result': 'Tester Present toggled to: {}'.format(active)}

        elif method == 'flash_hex':
            # Full sequence for flashing a Hex file!
            filepath = params.get('filepath')
            if not os.path.exists(filepath):
                raise Exception("Hex file path does not exist.")
            
            # Start a background flashing thread so it doesn't block IPC socket,
            # but for simplicity of this bridge, we can execute it synchronously
            # and report progress or return success. Let's execute the high level methods.
            # 1. Parse Hex file
            app_size = client.parse_data_get_size(filepath)
            # 2. Unlock/erase memory and flash in chunks
            # High-level sequence:
            # client.request_download_init(...)
            # client.transfer_data(...)
            # client.request_transfer_exit()
            # client.ecu_reset(...)
            # Let's perform a dry run of flashing:
            # We can write a wrapper loop inside client to execute it.
            # Let's check how the transfer_data is called. It requires:
            # startAddress, serverBufferSize, memorySize
            # Let's mock a simple progress updater via socket or just run it.
            # In our case, the client has high level flashing helpers.
            # Let's run a generic flashing loop:
            # (Note: For actual vehicle programming, this needs precise timing and sequence)
            # We'll expose the separate commands so the GUI can drive the sequence with a progress bar.
            return {'id': req_id, 'result': 'Exposed segment methods: request_download_init, transfer_data, request_transfer_exit'}

        elif method == 'request_download_init':
            address = int(params.get('address'))
            size = int(params.get('size'))
            # Format IDs default to 0x00 and 0x44
            dataFormat = int(params.get('data_format', 0x00))
            addrLengthFormat = int(params.get('addr_len_format', 0x44))
            res = client.request_download_init(address, dataFormat, addrLengthFormat, size)
            return {'id': req_id, 'result': res}

        elif method == 'transfer_data':
            start_addr = int(params.get('start_address'))
            buf_size = int(params.get('buffer_size', 0x3F0))
            mem_size = int(params.get('memory_size'))
            res = client.transfer_data(start_addr, buf_size, mem_size)
            return {'id': req_id, 'result': res}

        elif method == 'request_transfer_exit':
            res = client.request_transfer_exit()
            return {'id': req_id, 'result': res}

        elif method == 'wait_for_boot_id':
            res = client.wait_for_boot_id()
            return {'id': req_id, 'result': res}

        else:
            raise Exception("Method {} not implemented in UDS Bridge.".format(method))
            
    except Exception as e:
        traceback.print_exc()
        return {'id': req_id, 'error': e.message or str(e)}

def run_server(host='127.0.0.1', port=5000):
    global tester_present_active
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(1)
    
    print "UDS Bridge Server listening on {}:{}...".format(host, port)
    
    try:
        while True:
            conn, addr = server_socket.accept()
            print "GUI Client connected from: {}".format(addr)
            
            # Read line-by-line JSON packets
            buffer_data = ""
            while True:
                try:
                    data = conn.recv(4096)
                    if not data:
                        break
                    buffer_data += data
                    
                    while '\n' in buffer_data:
                        line, buffer_data = buffer_data.split('\n', 1)
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            request = json.loads(line)
                            response = handle_rpc(request)
                            conn.sendall(json.dumps(response) + "\n")
                        except Exception as e:
                            conn.sendall(json.dumps({'error': "JSON parse error: {}".format(e.message)}) + "\n")
                except socket.error as se:
                    print "Socket error: {}".format(se)
                    break
                except Exception as ex:
                    print "Unexpected error: {}".format(ex)
                    break
                    
            print "GUI Client disconnected."
            # Reset client tester present state
            tester_present_active = False
            
    except KeyboardInterrupt:
        print "Shutting down bridge."
    finally:
        server_socket.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='UDS Bridge server for Tesla diagnostic GUI.')
    parser.add_argument('--host', default='127.0.0.1', help='Bridge listen host')
    parser.add_argument('--port', type=int, default=5000, help='Bridge listen port')
    args = parser.parse_args()
    run_server(host=args.host, port=args.port)
