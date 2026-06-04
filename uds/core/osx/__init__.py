try:
    import udsClient
except ImportError:
    print "Compile core UDS client library for OS X and place it in this folder in order to use this module."
    import os
    print os.path.dirname(os.path.realpath(__file__))
    import sys
    sys.exit(0)