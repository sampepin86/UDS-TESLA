# Dynamically imports the SWIG-wrapped UDS core library for the current platform

import sys
if sys.platform.startswith('win'):
    from win.udsClient import *
elif sys.platform.startswith('linux'):
    from linux.udsClient import *
elif sys.platform.startswith('darwin'):
    from osx.udsClient import *