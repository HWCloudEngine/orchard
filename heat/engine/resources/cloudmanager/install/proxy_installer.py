import vm_installer_vcenter
import proxy_data

import log
import os
from oslo.config import cfg
import uuid

CONF = cfg.CONF
default_group = cfg.OptGroup(name='DEFAULT',
                             title='default config')
default_opts = [
    cfg.StrOpt('proxy_vm_type', default='vcenter')
]

CONF.register_group(default_group)
CONF.register_opts(default_opts, default_group)

vcenter_installer_group = cfg.OptGroup(name='VCENTER_INSTALLER',
                                       title='install a vm in vCenter')
vcenter_installer__opts = [
    cfg.StrOpt("ip", default=""),
    cfg.StrOpt("cluster", default=""),
    cfg.StrOpt("ds", default=""),
    cfg.StrOpt("proxy_image", default=""),
    cfg.StrOpt("user", default=""),
    cfg.StrOpt("pwd", default=""),
]
CONF.register_group(vcenter_installer_group)
CONF.register_opts(vcenter_installer__opts, vcenter_installer_group)

#CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
#absolute_config_file = os.path.join(CURRENT_PATH, "add_cloud.ini")
#CONF(["--config-file=%s" % absolute_config_file])

class proxy_installer(object):
    def __init__(self):
        self.data=proxy_data.data_handler()
        self.vm_type = CONF.DEFAULT.proxy_vm_type
        if self.vm_type == "vcenter":
            self.vcenter_ip=CONF.VCENTER_INSTALLER.ip
            self.vcenter_cluster=CONF.VCENTER_INSTALLER.cluster
            self.vcenter_ds=CONF.VCENTER_INSTALLER.ds
            self.vcenter_proxy_image=CONF.VCENTER_INSTALLER.proxy_image
            self.vcenter_user=CONF.VCENTER_INSTALLER.user
            self.vcenter_pwd=CONF.VCENTER_INSTALLER.pwd

    def _install(self):
        if self.vm_type == "vcenter":
            proxy_installer=vm_installer_vcenter.vm_installer_vcenter(self.vcenter_proxy_image,
                                                                      self.vcenter_ip+self.vcenter_cluster,
                                                                      self.vcenter_ds,
                                                                      self.vcenter_user,
                                                                      self.vcenter_pwd)

        need_create=False
        proxy_name=None
        self.data.lock()
        proxy_info=self.data.get_proxy_info()
        if proxy_info["total"]==0 or proxy_info["free"]==0:
            proxy_name="proxy_"+str(uuid.uuid1())
            #proxy_name="proxy_00"
            self.data.add_active_mem(proxy_name)
            need_create=True
        else:
            proxy_name=proxy_info["free_mems"][0]
            self.data.active_mem(proxy_name)
        self.data.unlock()

        if need_create:
            if proxy_installer._install_with_poweron(proxy_name) == -1:
                self.data.lock()
                self.data.remove_active_mem(proxy_name)
                self.data.unlock()

        return proxy_name

    def _uninstall(self, proxy_name):
        self.data.lock()
        self.data.free_mem(proxy_name)
        self.data.unlock()


def proxy_install():
    client = proxy_installer()
    return client._install()

def proxy_uninstall(proxy_id):
    client = proxy_installer()
    return client._uninstall(proxy_id)
