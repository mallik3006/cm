from cloudmesh.abstractclass.ComputeNodeABC import ComputeNodeABC
from pprint import pprint
from cloudmesh.common.Shell import Shell
from cloudmesh.common.dotdict import dotdict
from datetime import datetime
import io
import time
import subprocess
import sys
import shlex
import platform

import os
import textwrap
import webbrowser
from pprint import pprint
from cloudmesh.common.Shell import Shell
from cloudmesh.common.dotdict import dotdict
# from cloudmesh.abstractclass import ComputeNodeManagerABC
from cloudmesh.management.configuration.config import Config
from cloudmesh.common.console import Console
from cloudmesh.mongo import MongoDBController
from datetime import datetime
from cloudmesh.common.util import path_expand

"""
is vagrant up todate

==> vagrant: A new version of Vagrant is available: 2.2.4 (installed version: 2.2.2)!
==> vagrant: To upgrade visit: https://www.vagrantup.com/downloads.html
"""


class Provider(ComputeNodeABC):

    def run_command(self, command):
        process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
        while True:
            output = process.stdout.read(1)
            if output == b'' and process.poll() is not None:
                break
            if output:
                sys.stdout.write(output.decode("utf-8"))
                sys.stdout.flush()
        rc = process.poll()
        return rc

    def update_dict(self, entry, kind="node"):
        entry["kind"] = kind
        entry["driver"] = self.cloudtype
        entry["cloud"] = self.cloud
        return entry

    output = {
        'vm': {
            "sort_keys": ("name"),
            'order': ["vagrant.name",
                      "vagrant.cloud",
                      "vbox.name",
                      "vagrant.id",
                      "vagrant.provider",
                      "vagrant.state",
                      "vagrant.hostname"],
            'header': ["Name",
                       "Cloud",
                       "Vbox",
                       "Id",
                       "Provider",
                       "State",
                       "Hostname"]
        },
        'image': None,
        'flavor': None
    }

    def __init__(self, name=None,
                 configuration="~/.cloudmesh/.cloudmesh4.yaml"):
        self.config = Config()
        conf = Config(configuration)["cloudmesh"]
        self.user = conf["profile"]
        self.spec = conf["cloud"][name]
        self.cloud = name
        cred = self.spec["credentials"]
        self.cloudtype = self.spec["cm"]["kind"]

        # m = MongoDBController()
        # status = m.status()
        # if status.status == "error":
        #    raise Exception("ERROR: MongoDB is not running.")
        #
        # BUG: Naturally the following is wrong as it depends on the name.
        #
        # super().__init__("vagrant", config)

    def version(self):
        """
        This command returns the versions ov vagrant and virtual box
        :return: A dict with the information

        Description:

          The output looks like this



        """

        return None

    def images(self):

        return None

    def delete_image(self, name=None):
        result = ""
        if name is None:
            pass
            return "ERROR: please specify an image name"
            # read name form config
        else:
            try:
                command = "vagrant box remove {name}".format(name=name)
                result = Shell.execute(command, shell=True)
            except Exception as e:
                print(e)

            return result

    def add_image(self, name=None):

        command = "vagrant box add {name} --provider virtualbox".format(
            name=name)

        result = ""
        if name is None:
            pass
            return "ERROR: please specify an image name"
            # read name form config
        else:
            try:
                command = "vagrant box add {name} --provider virtualbox".format(
                    name=name)
                result = Shell.live(command)
                assert result.status == 0
            except Exception as e:
                print(e)
                print(result)
                print()

            return result

    def _check_version(self, r):
        """
        checks if vargarnt version is up to date

        :return:
        """
        return "A new version of Vagrant is available" not in r

    def start(self, name):
        """
        start a node

        :param name: the unique node name
        :return:  The dict representing the node
        """
        pass

    def create(self, **kwargs):

        return None

    def execute(self, name, command, cwd=None):
        return None

    def stop(self, name=None):
        """
        stops the node with the given name

        :param name:
        :return: The dict representing the node including updated status
        """
        pass

    def info(self, name=None):
        """
        gets the information of a node with a given name

        :param name:
        :return: The dict representing the node including updated status
        """

        return None

    def suspend(self, name=None):
        """
        suspends the node with the given name

        :param name: the name of the node
        :return: The dict representing the node
        """
        # TODO: find last name if name is None
        return None

    def resume(self, name=None):
        """
        resume the named node

        :param name: the name of the node
        :return: the dict of the node
        """
        # TODO: find last name if name is None
        return None

    def destroy(self, name=None):
        """
        Destroys the node
        :param name: the name of the node
        :return: the dict of the node
        """
        return None

    # @classmethod
    def delete(self, name=None):
        # TODO: check

        return None

    def dockerfile(self, **kwargs):

        arg = dotdict(kwargs)

        provision = kwargs.get("script", None)

        if provision is not None:
            arg.provision = 'config.vm.provision "shell", inline: <<-SHELL\n'
            for line in textwrap.dedent(provision).split("\n"):
                if line.strip() != "":
                    arg.provision += 12 * " " + "    " + line + "\n"
            arg.provision += 12 * " " + "  " + "SHELL\n"
        else:
            arg.provision = ""

        # not sure how I2 gets found TODO verify, comment bellow is not enough
        # the 12 is derived from the indentation of Vagrant in the script
        # TODO we may need not just port 80 to forward
        script = textwrap.dedent("""
               Vagrant.configure(2) do |config|

                 config.vm.define "{name}"
                 config.vm.hostname = "{name}"
                 config.vm.box = "{image}"
                 config.vm.box_check_update = true
                 config.vm.network "forwarded_port", guest: 80, host: {port}
                 config.vm.network "private_network", type: "dhcp"

                 # config.vm.network "public_network"
                 # config.vm.synced_folder "../data", "/vagrant_data"
                 config.vm.provider "virtualbox" do |vb|
                    # vb.gui = true
                    vb.memory = "{memory}"
                 end
                 {provision}
               end
           """.format(**arg))

        return script

    def _get_specification(self, cloud=None, name=None, port=None,
                           image=None, **kwargs):
        arg = dotdict(kwargs)
        arg.port = port
        config = Config()
        pprint(self.config)

        if cloud is None:
            #
            # TOD read default cloud
            #
            cloud = "vagrant"  # TODO must come through parameter or set cloud

        spec = config.data["cloudmesh"]["cloud"][cloud]
        default = spec["default"]
        pprint(default)

        if name is not None:
            arg.name = name
        else:
            # TODO get new name
            pass

        if image is not None:
            arg.image = image
        else:
            arg.image = default["image"]
            pass

        arg.path = default["path"]
        arg.directory = os.path.expanduser("{path}/{name}".format(**arg))
        arg.vagrantfile = "{directory}/Dockerfile".format(**arg)
        return arg

    def create_spec(self, name=None, image=None, size=1024, timeout=360,
                    port=80,
                    **kwargs):
        """
        creates a named node

        :param port:
        :param name: the name of the node
        :param image: the image used
        :param size: the size of the image
        :param timeout: a timeout in seconds that is invoked in case the image does not boot.
               The default is set to 3 minutes.
        :param kwargs: additional arguments passed along at time of boot
        :return:
        """
        """
        create one node
        """

        #
        # TODO BUG: if name contains not just letters and numbers and - return error, e. undersore not allowed
        #

        arg = self._get_specification(name=name,
                                      image=image,
                                      size=size,
                                      memory=size,
                                      timeout=timeout,
                                      port=port,
                                      **kwargs)

        if not os.path.exists(arg.directory):
            os.makedirs(arg.directory)

        configuration = self.vagrantfile(**arg)

        with open(arg.vagrantfile, 'w') as f:
            f.write(configuration)

        pprint(arg)

        return arg

    def list(self, raw=True):
        """
        list all nodes id
    
        :return: an array of dicts representing the nodes
        """
        return None

    def rename(self, name=None, destination=None):
        """
        rename a node
    
        :param destination:
        :param name: the current name
        :return: the dict with the new name
        """
        return None