# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

from vpn import VPN
from constant import *


class Cloud(object):

    def __init__(self, cloud_id, cascaded_openstack, api_vpn, tunnel_vpn, proxy_info=None, access="False"):
        """
        :param cascaded_openstack:  {"domain": "az32.singapore--aws.huawei.com","base_ip": "172.29.124.12",
                                    "tunnel_ip": "172.29.1.150", "api_ip": "172.29.0.150", "public_ip"}
        :param api_vpn: {"public_ip": "54.64.230.97","private_ip": "172.29.0.254", "private_subnet":"172.29.0.0/24"}
        :param tunnel_vpn: {"public_ip": "52.68.24.209","private_ip": "172.29.1.254", "private_subnet":"172.29.1.0/24"}
        """
        self.cloud_id = cloud_id
        self.cascaded_openstack = cascaded_openstack
        self.api_vpn = api_vpn
        self.tunnel_vpn = tunnel_vpn
        self.proxy_info = proxy_info
        self.access = access

    def config_openstack_vpn(self, openstack_api_gw, openstack_api_subnet,
                             openstack_tunnel_gw, openstack_tunnel_subnet):

        api_vpn = VPN(self.api_vpn["public_ip"], VpnConstant.AWS_VPN_ROOT, VpnConstant.AWS_VPN_ROOT_PWD)
        tunnel_vpn = VPN(self.tunnel_vpn["public_ip"], VpnConstant.AWS_VPN_ROOT, VpnConstant.AWS_VPN_ROOT_PWD)

        conn_name=self.get_vpn_conn_name()

        # 1. config remote vpn and restart remote vpn ipsec service
        api_vpn.copy_scripts()
        api_vpn.add_tunnel(conn_name["api_conn_name"],
                           self.api_vpn["public_ip"], self.api_vpn["private_subnet"],
                           openstack_api_gw, openstack_api_subnet)
        api_vpn.restart_ipsec_service()

        tunnel_vpn.copy_scripts()
        tunnel_vpn.add_tunnel(conn_name["tunnel_conn_name"],
                            self.tunnel_vpn["public_ip"], self.tunnel_vpn["private_subnet"],
                            openstack_tunnel_gw, openstack_tunnel_subnet)
        tunnel_vpn.restart_ipsec_service()

        return True

    def get_vpn_conn_name(self):
        api_conn_name = self.cloud_id + '-api'
        tunnel_conn_name = self.cloud_id + '-data'
        return {"api_conn_name": api_conn_name,"tunnel_conn_name": tunnel_conn_name}

    """
    def associate_remote_api_vpn(self, remote_api_vpn):
        if isinstance(remote_api_vpn, VPN):
            self.remote_api_vpn = remote_api_vpn
            return {"exitCode": cloudmanager.EXIT_CODE_SUCCESS}
        else:
            log.error("associate remote vpn error, remote_vpn is none")
            return {'exitCode': cloudmanager.EXIT_CODE_ERROR,
                    'error_message': "associate remote api vpn error, remote_vpn is none"}
    """

    """
    def associate_remote_data_vpn(self, remote_data_vpn):
        if isinstance(remote_data_vpn, VPN):
            self.remote_data_vpn = remote_data_vpn
            return {"exitCode": cloudmanager.EXIT_CODE_SUCCESS}
        else:
            log.error("associate remote vpn error, remote_vpn is none")
            return {'exitCode': cloudmanager.EXIT_CODE_ERROR,
                    'error_message': "associate remote data vpn error, remote_vpn is none"}
    """

    """
    def build_openstack_tunnel(self, tunnel_name, local_api_ip, local_api_subnet, local_data_ip, local_data_subnet, remote_api_ip, remote_api_subnet, remote_data_ip, remote_data_subnet):
        api_tunnel_name = tunnel_name + '-api'
        data_tunnel_name = tunnel_name + '-data'
        # 1. config local vpn and restart local vpn ipsec service
        # self.local_vpn.add_tunnel(api_tunnel_name, local_api_ip, local_api_subnet, remote_api_ip, remote_api_subnet)
        # self.local_vpn.add_tunnel(data_tunnel_name, local_data_ip, local_data_subnet, remote_data_ip, remote_data_subnet)
        # self.local_vpn.restart_ipsec_service()

        # 2. config remote vpn and restart remote vpn ipsec service
        self.remote_api_vpn.add_tunnel(api_tunnel_name, remote_api_ip, remote_api_subnet, local_api_ip, local_api_subnet)
        self.remote_api_vpn.restart_ipsec_service()
        self.remote_data_vpn.add_tunnel(data_tunnel_name, remote_data_ip, remote_data_subnet, local_data_ip, local_data_subnet)
        self.remote_data_vpn.restart_ipsec_service()

        # 3. up vpn tunnel
        self.local_vpn.up_tunnel(api_tunnel_name)
        self.local_vpn.up_tunnel(data_tunnel_name)

        # 4. check result

        return True
    """
