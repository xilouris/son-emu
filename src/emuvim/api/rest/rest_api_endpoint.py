import logging
import threading
from flask import Flask
from flask_restful import Api

# need to import total module to set its global variable dcs
import compute
from compute import dcs, ComputeList, ComputeStart, ComputeStatus, ComputeStop, DatacenterList, DatacenterStatus

# need to import total module to set its global variable net
import network
from network import NetworkAction

import monitor
from monitor import MonitorInterfaceAction, MonitorFlowAction

logging.basicConfig(level=logging.INFO)



class RestApiEndpoint(object):

    """
    Simple API endpoint that offers a REST
    interface. This interface will be used by the
    default command line client.
    """

    def __init__(self, listenip, port):
        self.ip = listenip
        self.port = port

        # setup Flask
        self.app = Flask(__name__)
        self.api = Api(self.app)

        # setup endpoints
        self.api.add_resource(ComputeList, "/restapi/compute/<dc_label>")
        self.api.add_resource(ComputeStart, "/restapi/compute/<dc_label>/<compute_name>/start")
        self.api.add_resource(ComputeStop, "/restapi/compute/<dc_label>/<compute_name>/stop")
        self.api.add_resource(ComputeStatus, "/restapi/compute/<dc_label>/<compute_name>")
        self.api.add_resource(DatacenterList, "/restapi/datacenter")
        self.api.add_resource(DatacenterStatus, "/restapi/datacenter/<dc_label>")

        self.api.add_resource(NetworkAction, "/restapi/network/<vnf_src_name>/<vnf_dst_name>")

        self.api.add_resource(MonitorInterfaceAction, "/restapi/monitor/<vnf_name>/<vnf_interface>/<metric>")
        self.api.add_resource(MonitorFlowAction, "/restapi/monitor/<vnf_name>/<vnf_interface>/<metric>/<cookie>")

        logging.debug("Created API endpoint %s(%s:%d)" % (self.__class__.__name__, self.ip, self.port))


    def connectDatacenter(self, dc):
        compute.dcs[dc.label] = dc
        logging.info("Connected DC(%s) to API endpoint %s(%s:%d)" % (dc.label, self.__class__.__name__, self.ip, self.port))

    def connectDCNetwork(self, DCnetwork):

        network.net = DCnetwork
        monitor.net = DCnetwork

        logging.info("Connected DCNetwork to API endpoint %s(%s:%d)" % (
            self.__class__.__name__, self.ip, self.port))

    def start(self):
        thread = threading.Thread(target= self._start_flask, args=())
        thread.daemon = True
        thread.start()
        logging.info("Started API endpoint @ http://%s:%d" % (self.ip, self.port))


    def _start_flask(self):
        self.app.run(self.ip, self.port, debug=True, use_reloader=False)