"""
Test suite to automatically test emulator REST API endpoints.
"""

import time
import unittest
from emuvim.test.api_base import SimpleTestTopology
import subprocess
from emuvim.dcemulator.node import EmulatorCompute
import ast

class testRestApi( SimpleTestTopology ):
    """
    Tests to check the REST API endpoints of the emulator.
    """

    def testRestApi(self):

        # create network
        self.createNet(nswitches=0, ndatacenter=2, nhosts=2, ndockers=0)

        # setup links
        self.net.addLink(self.dc[0], self.h[0])
        self.net.addLink(self.h[1], self.dc[1])
        self.net.addLink(self.dc[0], self.dc[1])

        # start api
        self.startApi()

        # start Mininet network
        self.startNet()

        print('->>>>>>> son-emu-cli compute start -d datacenter0 -n vnf1 ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call("son-emu-cli compute start -d datacenter0 -n vnf1", shell=True)
        print('->>>>>>> son-emu-cli compute start -d datacenter0 -n vnf2 ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call("son-emu-cli compute start -d datacenter0 -n vnf2", shell=True)
        print('->>>>>>> son-emu-cli compute start -d datacenter0 -n vnf3 ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call("son-emu-cli compute start -d datacenter1 -n vnf3", shell=True)
        subprocess.call("son-emu-cli compute list", shell=True)
        print('->>>>>>> checking running nodes, compute list, and connectivity >>>>>>>>>>')

        # check number of running nodes
        self.assertTrue(len(self.getContainernetContainers()) == 3)
        self.assertTrue(len(self.net.hosts) == 5)
        self.assertTrue(len(self.net.switches) == 2)

        # check compute list result
        self.assertTrue(len(self.dc[0].listCompute()) == 2)
        self.assertTrue(len(self.dc[1].listCompute()) == 1)
        self.assertTrue(isinstance(self.dc[0].listCompute()[0], EmulatorCompute))
        self.assertTrue(isinstance(self.dc[0].listCompute()[1], EmulatorCompute))
        self.assertTrue(isinstance(self.dc[1].listCompute()[0], EmulatorCompute))
        self.assertTrue(self.dc[0].listCompute()[1].name == "vnf1")
        self.assertTrue(self.dc[0].listCompute()[0].name == "vnf2")
        self.assertTrue(self.dc[1].listCompute()[0].name == "vnf3")

        # check connectivity by using ping
        self.assertTrue(self.net.ping([self.dc[0].listCompute()[1], self.dc[0].listCompute()[0]]) <= 0.0)
        self.assertTrue(self.net.ping([self.dc[0].listCompute()[0], self.dc[1].listCompute()[0]]) <= 0.0)
        self.assertTrue(self.net.ping([self.dc[1].listCompute()[0], self.dc[0].listCompute()[1]]) <= 0.0)

        print('network add vnf1 vnf2->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call("son-emu-cli network add -src vnf1 -dst vnf2 -b -c 10", shell=True)
        print('network remove vnf1 vnf2->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call("son-emu-cli network remove -src vnf1 -dst vnf2 -b", shell=True)

        print('>>>>> checking --> son-emu-cli compute stop -d datacenter0 -n vnf2 ->>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call("son-emu-cli compute stop -d datacenter0 -n vnf2", shell=True)

        # check number of running nodes
        self.assertTrue(len(self.getContainernetContainers()) == 2)
        self.assertTrue(len(self.net.hosts) == 4)
        self.assertTrue(len(self.net.switches) == 2)
        # check compute list result
        self.assertTrue(len(self.dc[0].listCompute()) == 1)
        self.assertTrue(len(self.dc[1].listCompute()) == 1)

        print('>>>>> checking --> son-emu-cli compute list ->>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call("son-emu-cli compute list", shell=True)
        output = subprocess.check_output("son-emu-cli compute list", shell=True)

        # check datacenter list result
        self.assertTrue("datacenter0" in output)

        print('>>>>> checking --> son-emu-cli compute status -d datacenter0 -n vnf1 ->>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call("son-emu-cli compute status -d datacenter0 -n vnf1", shell=True)
        output = subprocess.check_output("son-emu-cli compute status -d datacenter0 -n vnf1", shell=True)
        output= ast.literal_eval(output)

        # check compute status result
        self.assertTrue(output["name"] == "vnf1")
        self.assertTrue(output["state"]["Running"])

        print('>>>>> checking --> son-emu-cli datacenter list ->>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call("son-emu-cli datacenter list", shell=True)
        output = subprocess.check_output("son-emu-cli datacenter list", shell=True)

        # check datacenter list result

        self.assertTrue("datacenter0" in output)

        print('->>>>> checking --> son-emu-cli datacenter status -d datacenter0 ->>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call("son-emu-cli datacenter status -d datacenter0", shell=True)
        output = subprocess.check_output("son-emu-cli datacenter status -d datacenter0", shell=True)

        # check datacenter status result
        self.assertTrue("datacenter0" in output)

        self.stopNet()


if __name__ == '__main__':
    unittest.main()
