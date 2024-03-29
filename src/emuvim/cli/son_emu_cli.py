#!/usr/bin/python
"""
 Simple CLI client to interact with a running emulator.

 (c) 2016 by Manuel Peuster <manuel.peuster@upb.de>

 The CLI offers different tools, e.g., compute, network, ...
 Each of these tools is implemented as an independent Python
 module.

 cli compute start dc1 my_name flavor_a
 cli network create dc1 11.0.0.0/24
"""

import sys

from emuvim.cli import compute
from emuvim.cli import datacenter
from emuvim.cli import monitor
from emuvim.cli import network
from emuvim.cli.rest import compute as restcom
from emuvim.cli.rest import datacenter as restdc
from emuvim.cli.rest import monitor as restmon
from emuvim.cli.rest import network as restnetw


def main():
    if len(sys.argv) < 2:
        print("Usage: son-emu-cli <toolname> <arguments>")
        exit(0)
    if sys.argv[1] == "compute-zapi":
        compute.main(sys.argv[2:])
    elif sys.argv[1] == "network-zapi":
        network.main(sys.argv[2:])
    elif sys.argv[1] == "datacenter-zapi":
        datacenter.main(sys.argv[2:])
    elif sys.argv[1] == "monitor-zapi":
        monitor.main(sys.argv[2:])
    elif sys.argv[1] == "monitor":
        restmon.main(sys.argv[2:])
    elif sys.argv[1] == "network":
        restnetw.main(sys.argv[2:])
    elif sys.argv[1] == "compute":
        restcom.main(sys.argv[2:])
    elif sys.argv[1] == "datacenter":
        restdc.main(sys.argv[2:])


if __name__ == '__main__':
    main()
