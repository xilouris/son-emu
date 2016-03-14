"""
This module implements a simple REST API that behaves like SONATA's gatekeeper.

It is only used to support the development of SONATA's SDK tools and to demonstrate
the year 1 version of the emulator until the integration with WP4's orchestrator is done.
"""

import logging
import os
import uuid
import hashlib
import zipfile
import yaml
from docker import Client as DockerClient
from flask import Flask, request
import flask_restful as fr

LOG = logging.getLogger("sonata-dummy-gatekeeper")
LOG.setLevel(logging.DEBUG)
logging.getLogger("werkzeug").setLevel(logging.WARNING)


UPLOAD_FOLDER = "/tmp/son-dummy-gk/uploads/"
CATALOG_FOLDER = "/tmp/son-dummy-gk/catalog/"


class Gatekeeper(object):

    def __init__(self):
        self.services = dict()
        LOG.info("Create SONATA dummy gatekeeper.")

    def register_service_package(self, service_uuid, service):
        """
        register new service package
        :param service_uuid
        :param service object
        """
        self.services[service_uuid] = service
        # lets perform all steps needed to onboard the service
        service.onboard()


class Service(object):
    """
    This class represents a NS uploaded as a *.son package to the
    dummy gatekeeper.
    Can have multiple running instances of this service.
    """

    def __init__(self,
                 service_uuid,
                 package_file_hash,
                 package_file_path):
        self.uuid = service_uuid
        self.package_file_hash = package_file_hash
        self.package_file_path = package_file_path
        self.package_content_path = os.path.join(CATALOG_FOLDER, "services/%s" % self.uuid)
        self.manifest = None
        self.nsd = None
        self.vnfds = dict()
        self.local_docker_files = dict()
        self.instances = dict()

    def start_service(self, service_uuid):
        # TODO implement method
        # 1. parse descriptors
        # 2. do the corresponding dc.startCompute(name="foobar") calls
        # 3. store references to the compute objects in self.instantiations
        pass

    def onboard(self):
        """
        Do all steps to prepare this service to be instantiated
        :return:
        """
        # 1. extract the contents of the package and store them in our catalog
        self._unpack_service_package()
        # 2. read in all descriptor files
        self._load_package_descriptor()
        self._load_nsd()
        self._load_vnfd()
        self._load_docker_files()
        # 3. prepare container images (e.g. download or build Dockerfile)
        self._build_images_from_dockerfiles()
        self._download_predefined_dockerimages()

        LOG.info("On-boarded service: %r" % self.manifest.get("package_name"))

    def _unpack_service_package(self):
        """
        unzip *.son file and store contents in CATALOG_FOLDER/services/<service_uuid>/
        """
        with zipfile.ZipFile(self.package_file_path, "r") as z:
            z.extractall(self.package_content_path)

    def _load_package_descriptor(self):
        """
        Load the main package descriptor YAML and keep it as dict.
        :return:
        """
        self.manifest = load_yaml(
            os.path.join(
                self.package_content_path, "META-INF/MANIFEST.MF"))

    def _load_nsd(self):
        """
        Load the entry NSD YAML and keep it as dict.
        :return:
        """
        if "entry_service_template" in self.manifest:
            nsd_path = os.path.join(
                self.package_content_path,
                make_relative_path(self.manifest.get("entry_service_template")))
            self.nsd = load_yaml(nsd_path)
            LOG.debug("Loaded NSD: %r" % self.nsd.get("ns_name"))

    def _load_vnfd(self):
        """
        Load all VNFD YAML files referenced in MANIFEST.MF and keep them in dict.
        :return:
        """
        if "package_content" in self.manifest:
            for pc in self.manifest.get("package_content"):
                if pc.get("content-type") == "application/sonata.function_descriptor":
                    vnfd_path = os.path.join(
                        self.package_content_path,
                        make_relative_path(pc.get("name")))
                    vnfd = load_yaml(vnfd_path)
                    self.vnfds[vnfd.get("vnf_name")] = vnfd
                    LOG.debug("Loaded VNFD: %r" % vnfd.get("vnf_name"))

    def _load_docker_files(self):
        """
        Get all paths to Dockerfiles from MANIFEST.MF and store them in dict.
        :return:
        """
        if "package_content" in self.manifest:
            for df in self.manifest.get("package_content"):
                if df.get("content-type") == "application/sonata.docker_files":
                    docker_path = os.path.join(
                        self.package_content_path,
                        make_relative_path(df.get("name")))
                    # FIXME: Mapping to docker image names is hardcoded because of the missing mapping in the example package
                    self.local_docker_files[helper_map_docker_name(df.get("name"))] = docker_path
                    LOG.debug("Found Dockerfile: %r" % docker_path)

    def _build_images_from_dockerfiles(self):
        """
        Build Docker images for each local Dockerfile found in the package: self.local_docker_files
        """
        dc = DockerClient()
        LOG.info("Building %d Docker images (this may take several minutes) ..." % len(self.local_docker_files))
        for k, v in self.local_docker_files.iteritems():
            for line in dc.build(path=v.replace("Dockerfile", ""), tag=k, rm=False, nocache=False):
                LOG.debug("DOCKER BUILD: %s" % line)
            LOG.info("Docker image created: %s" % k)

    def _download_predefined_dockerimages(self):
        """
        If the package contains URLs to pre-build Docker images, we download them with this method.
        """
        # TODO implement
        pass


"""
Resource definitions and API endpoints
"""


class Packages(fr.Resource):

    def post(self):
        """
        Upload a *.son service package to the dummy gatekeeper.

        We expect request with a *.son file and store it in UPLOAD_FOLDER
        :return: UUID
        """
        try:
            # get file contents
            son_file = request.files['file']
            # generate a uuid to reference this package
            service_uuid = str(uuid.uuid4())
            file_hash = hashlib.sha1(str(son_file)).hexdigest()
            # ensure that upload folder exists
            ensure_dir(UPLOAD_FOLDER)
            upload_path = os.path.join(UPLOAD_FOLDER, "%s.son" % service_uuid)
            # store *.son file to disk
            son_file.save(upload_path)
            size = os.path.getsize(upload_path)
            # create a service object and register it
            s = Service(service_uuid, file_hash, upload_path)
            GK.register_service_package(service_uuid, s)
            # generate the JSON result
            return {"service_uuid": service_uuid, "size": size, "sha1": file_hash, "error": None}
        except Exception as ex:
            LOG.exception("Service package upload failed:")
            return {"service_uuid": None, "size": 0, "sha1": None, "error": "upload failed"}

    def get(self):
        """
        Return a list of UUID's of uploaded service packages.
        :return: dict/list
        """
        return {"service_uuid_list": list(GK.services.iterkeys())}


class Instantiations(fr.Resource):

    def post(self):
        """
        Instantiate a service specified by its UUID.
        Will return a new UUID to identify the running service instance.
        :return: UUID
        """
        # TODO implement method (start real service)
        json_data = request.get_json(force=True)
        service_uuid = json_data.get("service_uuid")
        if service_uuid is not None:
            service_instance_uuid = str(uuid.uuid4())
            LOG.info("Starting service %r" % service_uuid)
            return {"service_instance_uuid": service_instance_uuid}
        return None

    def get(self):
        """
        Returns a list of UUIDs containing all running services.
        :return: dict / list
        """
        # TODO implement method
        return {"service_instance_uuid_list": list()}


# create a single, global GK object
GK = Gatekeeper()
# setup Flask
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 512 * 1024 * 1024  # 512 MB max upload
api = fr.Api(app)
# define endpoints
api.add_resource(Packages, '/api/packages')
api.add_resource(Instantiations, '/api/instantiations')


def start_rest_api(host, port):
    # start the Flask server (not the best performance but ok for our use case)
    app.run(host=host,
            port=port,
            debug=True,
            use_reloader=False  # this is needed to run Flask in a non-main thread
            )


def ensure_dir(name):
    if not os.path.exists(name):
        os.makedirs(name)


def load_yaml(path):
    with open(path, "r") as f:
        try:
            r = yaml.load(f)
        except yaml.YAMLError as exc:
            LOG.exception("YAML parse error")
            r = dict()
    return r


def make_relative_path(path):
    if path.startswith("/"):
        return path.replace("/", "", 1)
    return path


def helper_map_docker_name(name):
    """
    Quick hack to fix missing dependency in example package.
    """
    # TODO remove this when package description is fixed
    mapping = {
        "/docker_files/iperf/Dockerfile": "iperf_docker",
        "/docker_files/firewall/Dockerfile": "fw_docker",
        "/docker_files/tcpdump/Dockerfile": "tcpdump_docker"
    }
    return mapping.get(name)


if __name__ == '__main__':
    """
    Lets allow to run the API in standalone mode.
    """
    logging.getLogger("werkzeug").setLevel(logging.INFO)
    start_rest_api("0.0.0.0", 8000)
