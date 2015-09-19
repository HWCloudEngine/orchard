# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

from cloud import Cloud


class AwsCloud(Cloud):

    def __init__(self, cloud_id, region, az, access_key_id, secret_key,
                 cascaded_openstack, api_vpn, tunnel_vpn, proxy_info=None, access="True"):
        """Initialize AwsCloud.
        """
        Cloud.__init__(self, cloud_id, cascaded_openstack, api_vpn, tunnel_vpn, proxy_info, access)
        self.region = region
        self.az = az
        self.access_key_id = access_key_id
        self.secret_key = secret_key

    """
    def connect_to_openstack(self, local_api_subnet, local_data_subnet, local_gw_ip):
        #connect to openstack system,.
        #   1. cloud will create remote vpn by self, and then build two vpn tunnel for api and data
        #   2. cloud will create openstack_host by self, and then config the host
        #   3. cloud will create openstack_proxy by self?
        #:return:
        # 1. cloud will create remote vpn by self,
        #   and then build two vpn tunnel for api and tunnel
        if self.local_vpn is None:
            log.error("local vpn is none, you must distribute local vpn first.")
            return {'exitCode': cloudmanager.EXIT_CODE_ERROR,
                    'error_message': 'local vpn is none, you must distribute local vpn first.'}

        if self.__install_remote_vpn__() is False:
            log.error("install remote vpn error.")
            return {'exitCode': cloudmanager.EXIT_CODE_ERROR, 'error_message': 'install remote vpn error.'}

        if self.build_openstack_tunnel(str(self.id), local_gw_ip, local_api_subnet, local_gw_ip, local_data_subnet, self.remote_api_vpn.public_ip, self.api_subnet, self.remote_data_vpn.public_ip, self.data_subnet) is False:
            log.error("build openstack tunnel error.")
            return {'exitCode': cloudmanager.EXIT_CODE_ERROR, 'error_message': 'build openstack tunnel error.'}

        # 2. install openstack_host and config

        # 3. install openstack_proxy and config




        return {'exitCode': cloudmanager.EXIT_CODE_SUCCESS}
    """

    """
    def install_openstack_vpn(self, api_subnet, data_subnet):

        pass

    def __install_remote_vpn__(self):
        log.info("install remote vpn, cloud_id = % s" % self.id)
        self.remote_api_vpn = VPN(uuid.uuid1(), "52.68.169.49", "root", "Galax0088@CLOUD8!")
        self.remote_data_vpn = VPN(uuid.uuid1(), "54.64.148.82", "root", "Galax0088@CLOUD8!")
        return True
    """

