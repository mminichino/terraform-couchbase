##
##

from lib.exceptions import *
from lib.aws import aws
from lib.gcp import gcp
from lib.azure import azure
from lib.vmware import vmware
from lib.location import location
from lib.template import template
from lib.varfile import varfile
from lib.cbrelmgr import cbrelease
from lib.ssh import ssh
from lib.toolbox import toolbox
from lib.invoke import tf_run
from lib.envmgr import envmgr
from lib.clustermgr import clustermgr
from lib.netmgr import network_manager
from lib.ask import ask
from lib.constants import CB_CFG_HEAD, CB_CFG_NODE, CB_CFG_TAIL, APP_CFG_HEAD, CLUSTER_CONFIG, APP_CONFIG


class run_manager(object):

    def __init__(self, parameters):
        self.cloud = parameters.cloud
        self.args = parameters
        self.lc = location()
        self.env = envmgr()
        self.var_template_file = 'variables.template'
        self.variable_file_name = 'variables.tf'
        self.lc.set_cloud(self.cloud)
        self.env.set_cloud(self.cloud)
        self.env.set_env(self.args.dev, self.args.test, self.args.prod, self.args.app)
        self.nm = network_manager(self.args)

    def build_env(self):
        inquire = ask()
        previous_tf_vars = None

        if self.cloud == 'aws':
            driver = aws()
            driver.aws_init()
        elif self.cloud == 'gcp':
            driver = gcp()
            driver.gcp_init()
            driver.gcp_prep(select=False)
        elif self.cloud == 'azure':
            driver = azure()
            driver.azure_init()
            driver.azure_prep()
        elif self.cloud == 'vmware':
            driver = vmware()
            driver.vmware_init()
            driver.vmware_set_cluster_name(self.env.get_cb_cluster_name(select=False))
            self.args.static = True
        else:
            raise RunMgmtError(f"unknown cloud {self.cloud}")

        env_text = self.env.get_env
        env_text = env_text.replace(':', ' ')

        print(f"Operating on environment {env_text}")
        self.env.create_env()

        t = template()
        v = varfile()
        c = cbrelease()
        s = ssh()
        b = toolbox()
        build_variables = []

        v.set_cloud(self.cloud)
        linux_type = v.get_linux_type()
        linux_release = v.get_linux_release()
        c.set_os_name(linux_type)
        c.set_os_ver(linux_release)

        var_file = self.env.env_dir + '/' + self.variable_file_name
        template_file = self.lc.tf_dir + '/' + self.var_template_file
        previous_tf_var_file = self.env.get_tf_var_file()
        if previous_tf_var_file:
            previous_tf_vars = t.read_variable_file(previous_tf_var_file)

        try:
            t.read_file(template_file)
            requested_vars = t.get_file_parameters()

            if previous_tf_vars:
                t.get_previous_values(v, previous_tf_vars, v.VARIABLES)
            pass_variables = t.process_vars(v, requested_vars, v.VARIABLES)
            build_variables = build_variables + pass_variables

            if previous_tf_vars:
                t.get_previous_values(c, previous_tf_vars, c.VARIABLES)
            pass_variables = t.process_vars(c, requested_vars, c.VARIABLES)
            build_variables = build_variables + pass_variables

            if previous_tf_vars:
                t.get_previous_values(s, previous_tf_vars, s.VARIABLES)
            pass_variables = t.process_vars(s, requested_vars, s.VARIABLES)
            build_variables = build_variables + pass_variables

            if previous_tf_vars:
                t.get_previous_values(b, previous_tf_vars, b.VARIABLES)
            pass_variables = t.process_vars(b, requested_vars, b.VARIABLES)
            build_variables = build_variables + pass_variables

            if previous_tf_vars:
                t.get_previous_values(self.nm, previous_tf_vars, self.nm.VARIABLES)
            pass_variables = t.process_vars(self.nm, requested_vars, self.nm.VARIABLES)
            build_variables = build_variables + pass_variables

            if previous_tf_vars:
                t.get_previous_values(self.env, previous_tf_vars, self.env.VARIABLES)
            pass_variables = t.process_vars(self.env, requested_vars, self.env.VARIABLES)
            build_variables = build_variables + pass_variables

            if previous_tf_vars:
                t.get_previous_values(driver, previous_tf_vars, driver.VARIABLES)
            pass_variables = t.process_vars(driver, requested_vars, driver.VARIABLES)
            build_variables = build_variables + pass_variables
        except Exception as err:
            RunMgmtError(f"can not process template {template_file}: {err}")

        print("Writing environment variables")

        try:
            t.process_template(build_variables)
            t.write_file(var_file)
        except Exception as err:
            ImageMgmtError(f"can not write packer variables {var_file}: {err}")

        cm = clustermgr(driver, self.env, self.nm, self.args)

        print("")
        if inquire.ask_yn('Create cluster configuration', default=True):
            print("")
            cm.create_node_config(CLUSTER_CONFIG, self.env.env_dir)

        print("")
        if self.env.app_env_dir:
            if inquire.ask_yn('Create app configuration', default=True):
                print("")
                cm.create_node_config(APP_CONFIG, self.env.app_env_dir)

        print("")
        print("Beginning environment deploy process")

        # try:
        #     tf = tf_run()
        #     tf.init(self.lc.packer_dir)
        # except Exception as err:
        #     ImageMgmtError(f"can not build image: {err}")