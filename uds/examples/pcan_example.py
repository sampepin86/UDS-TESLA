"""
 Usage of some UDS functions with PCAN transport layer

    @author trseroff
"""

try:
    # Make sure the module is installed and importable, otherwise print a message prompting installation.
    import uds
except ImportError:
    print "This example does not run from source unless the uds PyPi module is installed"
    print "Get it by running 'pip install --index-url https://artifactory.dev.teslamotors.com:443/artifactory/api/pypi/sysval-release-local/simple uds'"
    import sys
    sys.exit(0)

''' Core UDS Client Library and Node Data '''
from uds.client import Client
import uds.nodes as nodes

''' Set up message logger, if desired '''
from uds import TeslaUtilities

logger = TeslaUtilities.get_logger(TeslaUtilities.LoggingLevel.DEBUG, "example_log.txt", False,
                                   TeslaUtilities.LoggingHandler.FILE_HANDLER,
                                   TeslaUtilities.HandlerStream.STDERR)

''' Create PCAN transport layer and set up CAN tracer, if desired'''
from uds.transport.pcan_transport import PCANTransport, PCANTransportTraced, PB as PCANBasic

# With tracer:
transport = PCANTransportTraced("example_trace_file.trc", logger, PCANBasic.PCAN_USBBUS1, PCANBasic.PCAN_BAUD_500K)

# Without:
# transport = PCANTransport(bus=PCANBasic.PCAN_USBBUS1, baud=PCANBasic.PCAN_BAUD_500K)

try:
    transport.initialize()

    ''' Set up core UDS library and configure a node '''
    client = Client(transport, logger)
    client.set_node(nodes.NONE)

    ''' Use some UDS functions '''
    print "\n\n\n\t~~~Tester Present signals~~~"
    print client.tester_present(True)
    print "\n\n\n"
    print client.tester_present(True)
    print "\n\n\n"
    print client.tester_present(True)

    print "\n\n\n\t~~~Read Data ID 0x101~~~"
    print client.read_data(0x101, 3)

    # ''' Use the downloader sequence, if desired '''
    # print "\n\n\n\t~~~Starting download~~~"
    # from uds.sequences.tesla_v3_download import uds_download
    #
    # uds_download(client, "sample-hex-file-here.hex", logger=logger)
    # print "\n\n\n\t~~~Download complete~~~"

finally:
    ''' The CAN tracer creates a separate thread - call finish on it if you used that. '''
    transport.finish()

    # ''' The PCAN transport layer creates a separate thread too - call finish on it if you used it without a tracer. '''
    # transport.finish()
