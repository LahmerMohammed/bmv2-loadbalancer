import sys
import os

sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'utils'))

import p4runtime_lib.bmv2
import p4runtime_lib.helper
from p4runtime_lib.switch import ShutdownAllSwitchConnections

