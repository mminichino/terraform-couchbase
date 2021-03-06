##
##

import json
from lib.location import location
from lib.ask import ask
from lib.exceptions import *


class varfile(object):
    VARIABLES = [
        ('LINUX_RELEASE', 'os_linux_release', 'get_linux_release', None),
        ('LINUX_TYPE', 'os_linux_type', 'get_linux_type', None),
        ('OS_IMAGE_OWNER', 'os_image_owner', 'get_image_owner', None),
        ('OS_IMAGE_USER', 'os_image_user', 'get_image_user', None),
        ('OS_IMAGE_NAME', 'os_image_name', 'get_image_name', None),
        ('OS_IMAGE_FAMILY', 'os_image_family', 'get_image_family', None),
        ('OS_IMAGE_PUBLISHER', 'os_image_publisher', 'get_image_publisher', None),
        ('OS_IMAGE_SKU', 'os_image_sku', 'get_image_sku', None),
        ('OS_IMAGE_OFFER', 'os_image_offer', 'get_image_offer', None),
        ('OS_ISO_CHECKSUM', 'os_iso_checksum', 'get_iso_checksum', None),
        ('VMWARE_OS_TYPE', 'vm_guest_os_type', 'get_vmware_guest_type', None),
        ('OS_SW_URL', 'os_sw_url', 'get_sw_url', None),
    ]

    def __init__(self):
        self._global_vars: dict
        self._aws_packer_vars: dict
        self._aws_tf_vars: dict
        self._gcp_packer_vars: dict
        self._gcp_tf_vars: dict
        self._azure_packer_vars: dict
        self._azure_tf_vars: dict
        self._vmware_packer_vars: dict
        self._vmware_tf_vars: dict
        self.active_packer_vars = None
        self.active_tf_vars = None
        self.os_type = 'linux'
        self.os_name = None
        self.os_ver = None
        self.cloud = None
        self.image_owner = None
        self.image_user = None
        self.image_name = None
        self.image_family = None
        self.image_publisher = None
        self.image_offer = None
        self.image_sku = None
        self.iso_checksum = None
        self.sw_url = None
        self.vmware_guest_type = None
        self.var_file = None
        self.hcl_file = None

        self.lc = location()

        self._global_vars = self.get_var_data(self.lc.package_dir + '/globals.json')

        self._aws_packer_vars = self.get_var_data(self.lc.aws_packer + '/locals.json')
        self._aws_tf_vars = self.get_var_data(self.lc.aws_tf + '/locals.json')

        self._gcp_packer_vars = self.get_var_data(self.lc.gcp_packer + '/locals.json')
        self._gcp_tf_vars = self.get_var_data(self.lc.gcp_tf + '/locals.json')

        self._azure_packer_vars = self.get_var_data(self.lc.azure_packer + '/locals.json')
        self._azure_tf_vars = self.get_var_data(self.lc.azure_tf + '/locals.json')

        self._vmware_packer_vars = self.get_var_data(self.lc.vmware_packer + '/locals.json')
        self._vmware_tf_vars = self.get_var_data(self.lc.vmware_tf + '/locals.json')

    def get_var_data(self, file: str) -> dict:
        try:
            with open(file, 'r') as inputFile:
                var_text = inputFile.read()
                var_json = json.loads(var_text)
            inputFile.close()
            return var_json
        except Exception as err:
            raise VarFileError(f"Can not open var file {file}: {err}")

    def set_os_name(self, name: str):
        self.os_name = name

    def set_os_ver(self, release: str):
        self.os_ver = release

    def set_cloud(self, cloud: str):
        self.cloud = cloud

        if self.cloud == 'aws':
            self.active_packer_vars = self.aws_packer_vars
            self.active_tf_vars = self.aws_tf_vars
        elif self.cloud == 'gcp':
            self.active_packer_vars = self.gcp_packer_vars
            self.active_tf_vars = self.gcp_tf_vars
        elif self.cloud == 'azure':
            self.active_packer_vars = self.azure_packer_vars
            self.active_tf_vars = self.azure_tf_vars
        elif self.cloud == 'vmware':
            self.active_packer_vars = self.vmware_packer_vars
            self.active_tf_vars = self.vmware_tf_vars
        else:
            raise VarFileError(f"unknown cloud {self.cloud}")

    def aws_get_default(self, key: str) -> str:
        try:
            return self.aws_tf_vars['defaults'][key]
        except KeyError:
            raise VarFileError(f"value {key} not in aws defaults")

    def gcp_get_default(self, key: str) -> str:
        try:
            return self.gcp_tf_vars['defaults'][key]
        except KeyError:
            raise VarFileError(f"value {key} not in gcp defaults")

    def azure_get_default(self, key: str) -> str:
        try:
            return self.azure_tf_vars['defaults'][key]
        except KeyError:
            raise VarFileError(f"value {key} not in azure defaults")

    def vmware_get_default(self, key: str) -> str:
        try:
            return self.vmware_tf_vars['defaults'][key]
        except KeyError:
            raise VarFileError(f"value {key} not in vmware defaults")

    def get_all_os(self):
        os_list = []
        try:
            for key in self.active_packer_vars[self.os_type]:
                os_list.append(key)
            return os_list
        except KeyError:
            raise VarFileError(f"can not get {self.cloud} OS list of type {self.os_type}")

    def get_all_version(self) -> list[str]:
        release_list = []
        try:
            for i in range(len(self.active_packer_vars[self.os_type][self.os_name])):
                release_list.append(self.active_packer_vars[self.os_type][self.os_name][i]['version'])
            return release_list
        except KeyError:
            raise VarFileError(f"can not get {self.cloud} OS releases for {self.os_name}")

    def get_linux_release(self, default=None, write=None):
        inquire = ask()

        if write:
            self.os_ver = write
            return self.os_ver

        if self.os_ver:
            return self.os_ver

        version_list = self.get_all_version()
        selection = inquire.ask_list('Select Version', version_list, default=default)
        self.os_ver = version_list[selection]
        self.set_os_ver(self.os_ver)

        return self.os_ver

    def get_linux_type(self, default=None, write=None):
        inquire = ask()

        if write:
            self.os_name = write
            return self.os_name

        if self.os_name:
            return self.os_name

        distro_list = self.get_all_os()
        selection = inquire.ask_list('Select Linux Distribution', distro_list, default=default)
        self.os_name = distro_list[selection]
        self.set_os_name(self.os_name)

        return self.os_name

    def get_image_owner(self, write=None):
        if write:
            self.image_owner = write
            return self.image_owner

        self.image_owner = self.get_os_var('owner')
        return self.image_owner

    def get_image_user(self, write=None):
        if write:
            self.image_user = write
            return self.image_user

        self.image_user = self.get_os_var('user')
        return self.image_user

    def get_image_name(self, write=None):
        if write:
            self.image_name = write
            return self.image_name

        self.image_name = self.get_os_var('image')
        return self.image_name

    def get_image_family(self, write=None):
        if write:
            self.image_family = write
            return self.image_family

        self.image_family = self.get_os_var('family')
        return self.image_family

    def get_image_publisher(self, write=None):
        if write:
            self.image_publisher = write
            return self.image_publisher

        self.image_publisher = self.get_os_var('publisher')
        return self.image_publisher

    def get_image_offer(self, write=None):
        if write:
            self.image_offer = write
            return self.image_offer

        self.image_offer = self.get_os_var('offer')
        return self.image_offer

    def get_image_sku(self, write=None):
        if write:
            self.image_sku = write
            return self.image_sku

        self.image_sku = self.get_os_var('sku')
        return self.image_sku

    def get_iso_checksum(self, write=None):
        if write:
            self.iso_checksum = write
            return self.iso_checksum

        self.iso_checksum = self.get_os_var('checksum')
        return self.iso_checksum

    def get_sw_url(self, write=None):
        if write:
            self.sw_url = write
            return self.sw_url

        self.sw_url = self.get_os_var('sw_url')
        return self.sw_url

    def get_vmware_guest_type(self, write=None):
        if write:
            self.vmware_guest_type = write
            return self.vmware_guest_type

        self.vmware_guest_type = self.get_os_var('type')
        return self.vmware_guest_type

    def get_var_file(self, write=None):
        if write:
            self.var_file = write
            return self.var_file

        self.var_file = self.get_os_var('vars')
        return self.var_file

    def get_hcl_file(self, write=None):
        if write:
            self.hcl_file = write
            return self.hcl_file

        self.hcl_file = self.get_os_var('hcl')
        return self.hcl_file

    def get_os_var(self, key: str) -> str:
        try:
            for i in range(len(self.active_packer_vars[self.os_type][self.os_name])):
                if self.active_packer_vars[self.os_type][self.os_name][i]['version'] == self.os_ver:
                    return self.active_packer_vars[self.os_type][self.os_name][i][key]
        except KeyError:
            raise VarFileError(f"value {key} not in {self.cloud} packer variables for {self.os_name} {self.os_type}")

    def aws_get_os_var(self, key: str) -> str:
        try:
            for i in range(len(self.aws_packer_vars[self.os_type][self.os_name])):
                if self.aws_packer_vars[self.os_type][self.os_name][i]['version'] == self.os_ver:
                    return self.aws_packer_vars[self.os_type][self.os_name][i][key]
        except KeyError:
            raise VarFileError(f"value {key} not in aws packer variables for {self.os_name} {self.os_type}")

    def gcp_get_os_var(self, key: str) -> str:
        try:
            for i in range(len(self.gcp_packer_vars[self.os_type][self.os_name])):
                if self.gcp_packer_vars[self.os_type][self.os_name][i]['version'] == self.os_ver:
                    return self.gcp_packer_vars[self.os_type][self.os_name][i][key]
        except KeyError:
            raise VarFileError(f"value {key} not in gcp packer variables for {self.os_name} {self.os_type}")

    def azure_get_os_var(self, key: str) -> str:
        try:
            for i in range(len(self.azure_packer_vars[self.os_type][self.os_name])):
                if self.azure_packer_vars[self.os_type][self.os_name][i]['version'] == self.os_ver:
                    return self.azure_packer_vars[self.os_type][self.os_name][i][key]
        except KeyError:
            raise VarFileError(f"value {key} not in azure packer variables for {self.os_name} {self.os_type}")

    def vmware_get_os_var(self, key: str) -> str:
        try:
            for i in range(len(self.vmware_packer_vars[self.os_type][self.os_name])):
                if self.vmware_packer_vars[self.os_type][self.os_name][i]['version'] == self.os_ver:
                    return self.vmware_packer_vars[self.os_type][self.os_name][i][key]
        except KeyError:
            raise VarFileError(f"value {key} not in vmware packer variables for {self.os_name} {self.os_type}")

    @property
    def global_vars(self) -> dict:
        return self._global_vars

    @property
    def aws_packer_vars(self) -> dict:
        return self._aws_packer_vars

    @property
    def aws_tf_vars(self) -> dict:
        return self._aws_tf_vars

    @property
    def gcp_packer_vars(self) -> dict:
        return self._gcp_packer_vars

    @property
    def gcp_tf_vars(self) -> dict:
        return self._gcp_tf_vars

    @property
    def azure_packer_vars(self) -> dict:
        return self._azure_packer_vars

    @property
    def azure_tf_vars(self) -> dict:
        return self._azure_tf_vars

    @property
    def vmware_packer_vars(self) -> dict:
        return self._vmware_packer_vars

    @property
    def vmware_tf_vars(self) -> dict:
        return self._vmware_tf_vars
