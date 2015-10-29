# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

import os


class PublicConstant(object):
    SCRIPTS_DIR = os.path.join("/home/openstack/cloud_manager",
                               "scripts", "public")
    ADD_HOST_ADDRESS_SCRIPT = "add_host_address.sh"
    MODIFY_DNS_SERVER_ADDRESS = "modify_dns_server_address.sh"


class VpnConstant(object):
    VPN_ROOT = "root"
    VPN_ROOT_PWD = "hybrid@123"
    AWS_VPN_ROOT = "root"
    AWS_VPN_ROOT_PWD = "hybrid"
    SCRIPTS_DIR = os.path.join("/home/openstack/cloud_manager",
                               "scripts", "vpn")
    REMOTE_SCRIPTS_DIR = "/root/ipsec_config/"
    LIST_TUNNEL_SCRIPT = "list_tunnel.sh"
    ADD_TUNNEL_SCRIPT = "add_tunnel_ex.sh"
    REMOVE_TUNNEL_SCRIPT = "remove_tunnel.sh"


class Cascaded(object):
    ROOT = "root"
    ROOT_PWD = "cnp200@HW"
    SCRIPTS_DIR = os.path.join("/home/openstack/cloud_manager",
                               "scripts", "cascaded")
    REMOTE_SCRIPTS_DIR = "/root/cloud_manager/cascaded/"
    MODIFY_PROXY_SCRIPT = "modify_proxy.sh"
    MODIFY_CASCADED_SCRIPT = "modify_cascaded_domain.sh"
    MODIFY_CASCADED_SCRIPT_PY = "cascaded_handler.py"
    CASCADED_ADD_ROUTE_SCRIPT = "cascaded_add_route.sh"
    ADD_ROUTE_SCRIPT = "add_route.sh"
    ADD_API_ROUTE_SCRIPT = "cascaded_add_api_route.sh"
    CREATE_ENV = "create_env.sh"
    CONFIG_CINDER_SCRIPT = "config_storage.sh"
    CONFIG_CINDER_BACKUP_SCRIPT = "ceph_patch/backup_az.py"


class Cascading(object):
    ROOT = "root"
    ROOT_PWD = "Huawei@CLOUD8!"
    SCRIPTS_DIR = os.path.join("/home/openstack/cloud_manager",
                               "scripts", "cascading")
    REMOTE_SCRIPTS_DIR = "/root/cloud_manager/cascading/"
    CHECK_PROXY_SCRIPT = "check_free_proxy.sh"
    ADD_VPN_ROUTE_SCRIPT = "add_vpn_route.sh"
    KEYSTONE_ENDPOINT_SCRIPT = "keystone_endpoint_create.sh"
    ENABLE_OPENSTACK_SERVICE = "enable_openstack_service.sh"


class PatchesConstant(object):
    SCRIPTS_DIR = os.path.join("/home/openstack/cloud_manager",
                               "scripts", "patches")
    REMOTE_SCRIPTS_DIR = "/root/cloud_manager/patches/"
    CONFIG_PATCHES_SCRIPT = "config_patches_tool_config.sh"
    CONFIG_AWS_SCRIPT = "config_aws.sh"
    CONFIG_ROUTE_SCRIPT = "config_add_route.sh"


class RemoveConstant(object):
    SCRIPTS_DIR = os.path.join("/home/openstack/cloud_manager",
                               "scripts", "remove")
    REMOTE_SCRIPTS_DIR = "/root/cloud_manager/remove/"
    REMOVE_KEYSTONE_SCRIPT = "remove_keystone_endpoint.sh"
    REMOVE_PROXY_SCRIPT = "remove_proxy_host.sh"
    REMOVE_AGGREGATE_SCRIPT = "remove_aggregate.sh"
    REMOVE_CINDER_SERVICE_SCRIPT = "remove_cinder_service.sh"
    REMOVE_NEUTRON_AGENT_SCRIPT = "remove_neutron_agent.sh"


class CephConstant(object):
    USER = "ceph"
    PWD = "ceph@huawei"
    CEPH_INSTALL_SCRIPT = "/home/ceph/config-sh/install.sh"



