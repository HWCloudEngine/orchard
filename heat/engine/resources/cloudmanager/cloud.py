# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

from vpn import VPN
from constant import *


class Cloud(object):

    def __init__(self, cloud_id, cascaded_openstack, api_vpn, tunnel_vpn,
                 proxy_info=None, access="False"):
        """
        :param cascaded_openstack:  {"domain": "az32.singapore--aws.huawei.com",
                                     "base_ip": "172.29.124.12",
                                     "tunnel_ip": "172.29.1.150",
                                     "api_ip": "172.29.0.150",
                                     "public_ip": "52.0.0.1"}
        :param api_vpn: {"public_ip": "54.64.230.97",
                         "private_ip": "172.29.0.254",
                         "private_subnet":"172.29.0.0/24"}
        :param tunnel_vpn: {"public_ip": "52.68.24.209",
                            "private_ip": "172.29.1.254",
                            "private_subnet":"172.29.1.0/24"}
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
        return {"api_conn_name": api_conn_name,
                "tunnel_conn_name": tunnel_conn_name}


