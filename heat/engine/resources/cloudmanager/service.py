# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

import time
import log as logger
import constant
import awscloud
import install.cascaded_installer as cascaded_installer

from vpn import VPN
from commonutils import *
from environmentinfo import *
from awscloudpersist import AwsCloudDataHandler
from proxy_manager import ProxyManager
from subnet_manager import SubnetManager
from region_mapping import *
from constant import *


logger.init('CloudManager')


class CloudManager:

    def __init__(self):
        pass

    def add_remote_cloud(self, cloud_type, region_name, az, az_alias, access_key_id, secret_key, access="False"):
        """
        :param cloud_type:
        :param region_name:
        :param az:
        :param az_alias:
        :param access_key_id:
        :param secret_key:
        :param access:
        :return: True
        """
        logger.info("add cloud, cloud_type=%s, region_name=%s, az=%s, az_alias=%s, access=%s"
                    % (cloud_type, region_name, az, az_alias, access))
        try:
            env_info = read_environment_info()
        except ReadEnvironmentInfoFailure as e:
            logger.error("read environment info error. check the config file: %s" % e.message)
            return False

        if cloud_type == "AWS":

            # distribute cloud_domain && proxy_name for this cloud
            cascaded_domain = self.__distribute_cloud_domain__(region_name=region_name,
                                                               az_alias=az_alias,
                                                               az_tag="--aws")

            proxy_info = ProxyManager(env_info["cascading_ip"]).next_proxy_name()

            vpn_subnets = SubnetManager().distribute_subnet_pair()

            # before install, we must start proxy auto discovery on cascading host.
            # install base environment
            aws_cascaded_info = cascaded_installer.aws_cascaded_intall(region=get_region_id(region_name), az=az,
                                                                       access_key_id=access_key_id,
                                                                       secret_key=secret_key,
                                                                       api_cidr=vpn_subnets["api_subnet"],
                                                                       tunnel_cidr=vpn_subnets["tunnel_subnet"])
            # create a aws cloud instance.
            cascaded_openstack = aws_cascaded_info["cascaded_openstack"]
            cascaded_openstack["cascaded_domain"] = cascaded_domain

            api_vpn = aws_cascaded_info["cascaded_apivpn"]
            api_vpn["private_subnet"] = vpn_subnets["api_subnet"]

            tunnel_vpn = aws_cascaded_info["cascaded_tunnelvpn"]
            tunnel_vpn["private_subnet"] = vpn_subnets["tunnel_subnet"]

            cloud = awscloud.AwsCloud(cascaded_domain, get_region_id(region_name), az, access_key_id, secret_key,
                                      cascaded_openstack, api_vpn, tunnel_vpn, access=access.lower())

            # config local_vpn.
            vpn_conn_name = cloud.get_vpn_conn_name()
            api_vpn["conn_name"] = vpn_conn_name["api_conn_name"]
            tunnel_vpn["conn_name"] = vpn_conn_name["tunnel_conn_name"]

            local_vpn = VPN(env_info["vpn_ip"], constant.VpnConstant.VPN_ROOT, constant.VpnConstant.VPN_ROOT_PWD)
            local_vpn.add_tunnel(api_vpn["conn_name"],
                                 env_info["api_public_gw"], env_info["api_subnet"],
                                 cloud.api_vpn["public_ip"], cloud.api_vpn["private_subnet"])
            local_vpn.add_tunnel(tunnel_vpn["conn_name"],
                                 env_info["tunnel_public_gw"], env_info["tunnel_subnet"],
                                 cloud.tunnel_vpn["public_ip"], cloud.tunnel_vpn["private_subnet"])

            # retart local vpn
            local_vpn.restart_ipsec_service()

            # config cloud vpn
            self.__check_host_status__(host=api_vpn["public_ip"],
                                       user=constant.VpnConstant.AWS_VPN_ROOT,
                                       password=constant.VpnConstant.AWS_VPN_ROOT_PWD)
            self.__check_host_status__(host=tunnel_vpn["public_ip"],
                                       user=constant.VpnConstant.AWS_VPN_ROOT,
                                       password=constant.VpnConstant.AWS_VPN_ROOT_PWD)
            cloud.config_openstack_vpn(env_info["api_public_gw"], env_info["api_subnet"],
                                       env_info["tunnel_public_gw"], env_info["tunnel_subnet"])

            # up vpn tunnel
            # local_vpn.up_tunnel(api_vpn["conn_name"], tunnel_vpn["conn_name"])

            self.__add_cascading_vpn_route__(cascading_ip=env_info["cascading_ip"],
                                             aws_api_subnet=api_vpn["private_subnet"],
                                             api_gw=env_info["api_vpn_ip"],
                                             aws_tunnel_subnet=tunnel_vpn["private_subnet"],
                                             tunnel_gw=env_info["tunnel_vpn_ip"])

            # config proxy on cascading host
            if proxy_info is None:
                proxy_info = self.__get_proxy_retry__(env_info["cascading_ip"])

            cloud.proxy_info = proxy_info
            proxy_host_name = proxy_info["host_name"]
            proxy_num = proxy_info["proxy_num"]
            logger.debug("proxy_host_name = %s, proxy_num = %s" % (proxy_host_name, proxy_num))

            self.__config_proxy__(env_info["cascading_ip"], proxy_info)

            AwsCloudDataHandler().add_aws_cloud(cloud)

            # config cascading
            self.__config_cascading__(env_info, cascaded_openstack)

            # config az_cascaded
            self.__check_host_status__(host=cascaded_openstack["tunnel_ip"],
                                       user=constant.Cascaded.ROOT,
                                       password=constant.Cascaded.ROOT_PWD)

            self.__config_az_cascaded__(env_info, cascaded_openstack)

            self.__config_patch_tools__(cascading_ip=env_info["cascading_ip"], proxy_num=proxy_num,
                                        proxy_host_name=proxy_host_name,
                                        cascaded_domain=cascaded_domain,
                                        openstack_api_subnet=env_info["api_subnet"],
                                        aws_api_gw=api_vpn["private_ip"],
                                        openstack_tunnel_subnet=env_info["tunnel_subnet"],
                                        aws_tunnel_gw=tunnel_vpn["private_ip"],
                                        cascading_domain=env_info["cascading_domain"])

            self.__config_aws_patches__(cascading_ip=env_info["cascading_ip"],
                                        openstack_api_subnet=env_info["api_subnet"],
                                        aws_api_gw=api_vpn["private_ip"],
                                        openstack_tunnel_subnet=env_info["tunnel_subnet"],
                                        aws_tunnel_gw=tunnel_vpn["private_ip"],
                                        cascaded_ip=cascaded_openstack["api_ip"],
                                        region=cloud.region, az=cloud.az,
                                        access_key_id=cloud.access_key_id,
                                        secret_key=cloud.secret_key,
                                        api_subnet_id=aws_cascaded_info["subnet_info"]["api_subnet"],
                                        tunnel_subnet_id=aws_cascaded_info["subnet_info"]["tunnel_subnet"])

            self.__deploy_patches__(cascading_ip=env_info["cascading_ip"], cascaded_openstack=cascaded_openstack)

            if access.lower() == "true":
                try:
                    self.__enable_network_cross__(cloud=cloud,
                                                  access_key_id=access_key_id,
                                                  secret_key=secret_key,)
                except Exception:
                    pass

            logger.info("success...")

            return True

        elif cloud_type == "vcloud":
            # add vmware cloud
            pass

    def __distribute_cloud_domain__(self, region_name, az_alias, az_tag):
        """distribute cloud domain
        :return:
        """
        domainpostfix = "huawei.com"
        l_region_name=region_name.lower()
        domain = ".".join([az_alias, l_region_name+az_tag, domainpostfix])
        return domain
        # return "az34.%s.huawei.com" % az
        # return "az32.singapore--aws.huawei.com"

    def __check_host_status__(self, host, user, password):
        for i in range(100):
            if check_ssh_server(host=host, user=user, password=password):
                return True
            else:
                time.sleep(5)
        logger.error("check host status error, host = % s" % host)
        raise ConfigVPNFailure(reason="check host status error, host = % s" % host)

    def __add_cascading_vpn_route__(self, cascading_ip, aws_api_subnet, api_gw, aws_tunnel_subnet, tunnel_gw):

        # ssh = sshclient.SSH(host=cascading_ip, user=constant.Cascading.ROOT, password=constant.Cascading.ROOT_PWD)

        scp_file_to_host(host=cascading_ip, user=constant.Cascading.ROOT, password=constant.Cascading.ROOT_PWD,
                         file_name=constant.Cascading.ADD_VPN_ROUTE_SCRIPT,
                         local_dir=constant.Cascading.SCRIPTS_DIR,
                         remote_dir=constant.Cascading.REMOTE_SCRIPTS_DIR)

        execute_cmd_without_stdout(host=cascading_ip,
                                   user=constant.Cascading.ROOT, password=constant.Cascading.ROOT_PWD,
                                   cmd='cd %(dir)s; sh %(script)s '
                                       '%(aws_api_subnet)s %(api_gw)s %(aws_tunnel_subnet)s %(tunnel_gw)s'
                                   % {"dir": constant.Cascading.REMOTE_SCRIPTS_DIR,
                                      "script": constant.Cascading.ADD_VPN_ROUTE_SCRIPT,
                                      "aws_api_subnet": aws_api_subnet, "api_gw": api_gw,
                                      "aws_tunnel_subnet": aws_tunnel_subnet, "tunnel_gw": tunnel_gw})
        return True

    """
    now wu do not use it @ 2015.8.22
    def __start_proxy_auto_discovery__(self, cascading_ip):
        ssh = sshclient.SSH(host=cascading_ip, user=constant.Cascading.ROOT, password=constant.Cascading.ROOT_PWD)

        scp_file_to_host(ssh, constant.Cascading.PROXY_DISCOVERY_SCRIPT,
                         constant.Cascading.SCRIPTS_DIR, constant.Cascading.REMOTE_SCRIPTS_DIR)

        execute_cmd_without_stdout(ssh, 'cd %(dir)s; sh %(script)s > result.log &'
                                          % {"dir": constant.Cascading.REMOTE_SCRIPTS_DIR,
                                             "script": constant.Cascading.PROXY_DISCOVERY_SCRIPT})

        return True
    """

    def __get_proxy_retry__(self, cascading_ip):
        logger.info("get proxy retry ...")
        proxy_info = ProxyManager(cascading_ip).next_proxy_name();
        for i in range(10):
            if proxy_info is None:
                time.sleep(20)
                proxy_info = ProxyManager().next_proxy_name();
            else:
                return proxy_info
        raise ConfigProxyFailure(reason="check proxy config result failed")

    """
    def __check_proxy_config_result__(self, cascading_ip):
        # run auto_find_proxy.sh on cascading
        logger.info("check proxy config result ...")
        ssh = sshclient.SSH(host=cascading_ip, user=constant.Cascading.ROOT, password=constant.Cascading.ROOT_PWD)
        proxy_host_name = None
        for i in range(1, 10):
            time.sleep(1)
            try:
                proxy_host_name = execute_cmd_with_stdout(ssh, 'cd %(dir)s; sh %(script)s check'
                                                          % {"dir": constant.Cascading.REMOTE_SCRIPTS_DIR,
                                                             "script": constant.Cascading.PROXY_DISCOVERY_SCRIPT})
            except SSHCommandFailure as e:
                logger.info("check proxy config result failed, time = %s, proxy_host_name = %s" % (i, proxy_host_name))

            if proxy_host_name is not None:
                break

        if proxy_host_name is not None:
            return proxy_host_name.strip('\n')

        raise ConfigProxyFailure(reason="check proxy config result failed")
    """

    def __config_proxy__(self, cascading_ip, proxy_info):
        logger.info("command role host add...")
        execute_cmd_without_stdout(host=cascading_ip, user=constant.Cascading.ROOT, password=constant.Cascading.ROOT_PWD,
                                   cmd="cps role-host-add --host %(proxy_host_name)s dhcp; cps commit"
                                       % {"proxy_host_name": proxy_info["host_name"]})
        return True

    def __config_az_cascaded__(self, env_info, cascaded_openstack):
        logger.info("cascaded host is ready, start config")
        cascaded_ip = cascaded_openstack["tunnel_ip"]
        # execute_cmd_without_stdout(host=cascaded_ip, user=constant.Cascaded.ROOT, password=constant.Cascaded.ROOT_PWD,
        #                            cmd='mkdir -p %(dir)s' % {"dir": constant.Cascaded.REMOTE_SCRIPTS_DIR})

        # modify dns server address
        address = "/%(cascading_domain)s/%(cascading_ip)s,/%(cascaded_domain)s/%(cascaded_ip)s" \
                  % {"cascading_domain": env_info["cascading_domain"],
                     "cascading_ip": env_info["cascading_ip"],
                     "cascaded_domain": cascaded_openstack["cascaded_domain"],
                     "cascaded_ip": cascaded_openstack["api_ip"]}

        scp_file_to_host(host=cascaded_ip, user=constant.Cascaded.ROOT, password=constant.Cascaded.ROOT_PWD,
                         file_name=constant.PublicConstant.MODIFY_DNS_SERVER_ADDRESS,
                         local_dir=constant.PublicConstant.SCRIPTS_DIR,
                         remote_dir=constant.Cascaded.REMOTE_SCRIPTS_DIR)

        for i in range(30):
            try:
                execute_cmd_without_stdout(host=cascaded_ip,
                                           user=constant.Cascaded.ROOT,
                                           password=constant.Cascaded.ROOT_PWD,
                                           cmd='cd %(dir)s; sh %(script)s replace %(address)s'
                                               % {"dir": constant.Cascaded.REMOTE_SCRIPTS_DIR,
                                                  "script": constant.PublicConstant.MODIFY_DNS_SERVER_ADDRESS,
                                                  "address": address})
                break
            except SSHCommandFailure as e:
                logger.error("modify cascaded dns address error: %s" % e.format_message())
                time.sleep(10)

        # modify apach proxy on cascaded
        scp_file_to_host(host=cascaded_ip, user=constant.Cascaded.ROOT, password=constant.Cascaded.ROOT_PWD,
                         file_name=constant.Cascaded.MODIFY_PROXY_SCRIPT,
                         local_dir=constant.Cascaded.SCRIPTS_DIR,
                         remote_dir=constant.Cascaded.REMOTE_SCRIPTS_DIR)

        gateway = self.__get_gateway__(cascaded_openstack["api_ip"])

        for i in range(7):
            try:
                execute_cmd_without_stdout(host=cascaded_ip, user=constant.Cascaded.ROOT,
                                           password=constant.Cascaded.ROOT_PWD,
                                           cmd='cd %(dir)s; sh %(script)s %(cascaded_ip)s %(cascaded_gw)s'
                                               % {"dir": constant.Cascaded.REMOTE_SCRIPTS_DIR,
                                                  "script": constant.Cascaded.MODIFY_PROXY_SCRIPT,
                                                  "cascaded_ip": cascaded_openstack["api_ip"],
                                                  "cascaded_gw": gateway})
                break
            except SSHCommandFailure as e:
                logger.error("modify cascaded proxy error: %s" % e.format_message())
                time.sleep(3)

        # config cascaded domain
        scp_file_to_host(host=cascaded_ip, user=constant.Cascaded.ROOT, password=constant.Cascaded.ROOT_PWD,
                         file_name=constant.Cascaded.MODIFY_CASCADED_SCRIPT,
                         local_dir=constant.Cascaded.SCRIPTS_DIR,
                         remote_dir=constant.Cascaded.REMOTE_SCRIPTS_DIR)

        for i in range(7):
            try:
                execute_cmd_without_stdout(host=cascaded_ip, user=constant.Cascaded.ROOT,
                                           password=constant.Cascaded.ROOT_PWD,
                                           cmd='cd %(dir)s; sh %(script)s %(cascading_domain)s %(cascaded_domain)s'
                                               % {"dir": constant.Cascaded.REMOTE_SCRIPTS_DIR,
                                                  "script": constant.Cascaded.MODIFY_CASCADED_SCRIPT,
                                                  "cascading_domain": env_info["cascading_domain"],
                                                  "cascaded_domain": cascaded_openstack["cascaded_domain"]})
                break
            except SSHCommandFailure as e:
                logger.error("modify cascaded domain error: %s" % e.format_message())
                time.sleep(3)


        # add cascaded route
        # scp_file_to_host(host=cascaded_ip, user=constant.Cascaded.ROOT, password=constant.Cascaded.ROOT_PWD,
        #                  file_name=constant.Cascaded.CASCADED_ADD_ROUTE_SCRIPT,
        #                  local_dir=constant.Cascaded.SCRIPTS_DIR,
        #                  remote_dir=constant.Cascaded.REMOTE_SCRIPTS_DIR)
        #
        # execute_cmd_without_stdout(host=cascaded_ip, user=constant.Cascaded.ROOT, password=constant.Cascaded.ROOT_PWD,
        #                            cmd='cd %(dir)s; sh %(script)s %(openstack_api_subnet)s %(aws_api_gw)s '
        #                                '%(openstack_tunnel_subnet)s %(aws_tunnel_gw)s'
        #                            % {"dir": constant.Cascaded.REMOTE_SCRIPTS_DIR,
        #                               "script": constant.Cascaded.CASCADED_ADD_ROUTE_SCRIPT,
        #                               "openstack_api_subnet": env_info["api_subnet"],
        #                               "aws_api_gw": api_vpn["private_ip"],
        #                               "openstack_tunnel_subnet": env_info["tunnel_subnet"],
        #                               "aws_tunnel_gw":tunnel_vpn["private_ip"]})
        return True

    def __config_cascading__(self, env_info, cascaded_openstack):
        # config on cascading
        cascading_ip=env_info["cascading_ip"]
        # execute_cmd_without_stdout(host=cascading_ip, user=constant.Cascading.ROOT,password=constant.Cascading.ROOT_PWD,
        #                            cmd='mkdir -p %(dir)s' % {"dir": constant.Cascading.REMOTE_SCRIPTS_DIR})

        # modify dns server address
        address = "/%(cascaded_domain)s/%(cascaded_ip)s"\
                  % {"cascaded_domain": cascaded_openstack["cascaded_domain"],
                     "cascaded_ip": cascaded_openstack["api_ip"]}

        # scp_file_to_host(host=cascading_ip, user=constant.Cascading.ROOT, password=constant.Cascading.ROOT_PWD,
        #                  file_name=constant.PublicConstant.MODIFY_DNS_SERVER_ADDRESS,
        #                  local_dir=constant.PublicConstant.SCRIPTS_DIR,
        #                  remote_dir=constant.Cascading.REMOTE_SCRIPTS_DIR)

        for i in range(3):
            try:
                execute_cmd_without_stdout(host=cascading_ip, user=constant.Cascading.ROOT,
                                           password=constant.Cascading.ROOT_PWD,
                                           cmd='cd %(dir)s; sh %(script)s add %(address)s'
                                               % {"dir": constant.Cascading.REMOTE_SCRIPTS_DIR,
                                                  "script": constant.PublicConstant.MODIFY_DNS_SERVER_ADDRESS,
                                                  "address": address})
                break
            except SSHCommandFailure as e:
                logger.error("modify cascading dns address error: %s" % e.format_message())
                time.sleep(3)

        # config keystone
        # scp_file_to_host(host=cascading_ip, user=constant.Cascading.ROOT, password=constant.Cascading.ROOT_PWD,
        #                  file_name=constant.Cascading.KEYSTONE_ENDPOINT_SCRIPT,
        #                  local_dir=constant.Cascading.SCRIPTS_DIR,
        #                  remote_dir=constant.Cascading.REMOTE_SCRIPTS_DIR)

        for i in range(3):
            try:
                execute_cmd_without_stdout(host=cascading_ip, user=constant.Cascading.ROOT,
                                           password=constant.Cascading.ROOT_PWD,
                                           cmd='. %(env)s; cd %(dir)s; sh %(script)s %(cascaded_domain)s'
                                               % {"env": env_info["env"], "dir": constant.Cascading.REMOTE_SCRIPTS_DIR,
                                                  "script": constant.Cascading.KEYSTONE_ENDPOINT_SCRIPT,
                                                  "cascaded_domain": cascaded_openstack["cascaded_domain"]})
                break
            except SSHCommandFailure as e:
                logger.error("create keystone endpoint error: %s" % e.format_message())
                time.sleep(3)

        return True


    def __config_patch_tools__(self, cascading_ip, proxy_num, proxy_host_name, cascaded_domain,
                               openstack_api_subnet, aws_api_gw,
                               openstack_tunnel_subnet, aws_tunnel_gw, cascading_domain):
        execute_cmd_without_stdout(host=cascading_ip, user=constant.Cascading.ROOT, password=constant.Cascading.ROOT_PWD,
                                   cmd='cd %(dis)s; sh %(script)s '
                                       '%(proxy_num)s %(proxy_host_name)s %(cascaded_domain)s '
                                       '%(openstack_api_subnet)s %(aws_api_gw)s '
                                       '%(openstack_tunnel_subnet)s %(aws_tunnel_gw)s %(cascading_domain)s'
                                   % {"dis": constant.PatchesConstant.REMOTE_SCRIPTS_DIR,
                                      "script": constant.PatchesConstant.CONFIG_PATCHES_SCRIPT,
                                      "proxy_num":proxy_num, "proxy_host_name": proxy_host_name,
                                      "cascaded_domain":  cascaded_domain,
                                      "openstack_api_subnet": openstack_api_subnet, "aws_api_gw": aws_api_gw,
                                      "openstack_tunnel_subnet": openstack_tunnel_subnet,
                                      "aws_tunnel_gw": aws_tunnel_gw, "cascading_domain": cascading_domain})
        return True

    def __config_aws_patches__(self, cascading_ip, cascaded_ip,
                               region, az, access_key_id, secret_key,
                               api_subnet_id, tunnel_subnet_id,
                               openstack_api_subnet, aws_api_gw,
                               openstack_tunnel_subnet, aws_tunnel_gw,
                               dns="162.3.116.72", cgw_id="i-c124700d", cgw_ip="52.74.238.254"):

        execute_cmd_without_stdout(host=cascading_ip, user=constant.Cascading.ROOT, password=constant.Cascading.ROOT_PWD,
                                   cmd='cd /root/cloud_manager/patches; '
                                       'sh config_aws.sh %s %s %s %s %s %s %s %s %s %s %s %s %s %s'
                                   % (dns, access_key_id, secret_key, region, az,
                                      api_subnet_id, tunnel_subnet_id, cgw_id, cgw_ip, cascaded_ip,
                                      openstack_api_subnet, aws_api_gw,
                                      openstack_tunnel_subnet, aws_tunnel_gw))
        execute_cmd_without_stdout(host=cascading_ip, user=constant.Cascading.ROOT, password=constant.Cascading.ROOT_PWD,
                                   cmd='cd /root/cloud_manager/patches; sh config_add_route.sh %s %s %s %s'
                                   % (openstack_api_subnet, aws_api_gw,
                                      openstack_tunnel_subnet, aws_tunnel_gw))
        return True

    def __deploy_patches__(self, cascading_ip,  cascaded_openstack):
        time.sleep(5)
        execute_cmd_without_stdout(host=cascading_ip, user=constant.Cascading.ROOT, password=constant.Cascading.ROOT_PWD,
                                   cmd='cd /root/cloud_manager/patches/patches_tool; python config.py cascading')
        time.sleep(5)
        execute_cmd_without_stdout(host=cascading_ip, user=constant.Cascading.ROOT, password=constant.Cascading.ROOT_PWD,
                                   cmd='cd /root/cloud_manager/patches/patches_tool; python config.py prepare')
        time.sleep(5)
        execute_cmd_without_stdout(host=cascading_ip, user=constant.Cascading.ROOT, password=constant.Cascading.ROOT_PWD,
                                   cmd='cd /root/cloud_manager/patches/patches_tool; python patches_tool.py')

        cascaded_ip = cascaded_openstack["tunnel_ip"]

        for i in range(3):
            try:
                time.sleep(5)
                execute_cmd_without_stdout(host=cascaded_ip, user=constant.Cascaded.ROOT,
                                           password=constant.Cascaded.ROOT_PWD,
                                           cmd='cd %(dir)s; python %(script)s aws_config.ini'
                                               % {"dir": "/home/fsp/patches_tool/aws_patch",
                                                  "script": "patch_file.py"})
                break
            except SSHCommandFailure as e:
                logger.error("patch awspatch error: %s" % e.format_message())
                time.sleep(5)
                execute_cmd_without_stdout(host=cascading_ip,
                                           user=constant.Cascading.ROOT,
                                           password=constant.Cascading.ROOT_PWD,
                                           cmd='cd /root/cloud_manager/patches/patches_tool; python config.py prepare')
                continue

        return True

    def __get_gateway__(self, ip, mask=None):
        arr=ip.split(".")
        gateway="%s.%s.%s.1" % (arr[0], arr[1], arr[2])
        return gateway

    def __enable_network_cross__(self, cloud, access_key_id, secret_key):
        vpn_info = cloud.tunnel_vpn
        cascaded_info = cloud.cascaded_openstack
        vpn = VPN(public_ip=vpn_info["public_ip"],
                  user=VpnConstant.AWS_VPN_ROOT,
                  pass_word=VpnConstant.AWS_VPN_ROOT_PWD)

        for cloud_id in AwsCloudDataHandler().list_aws_clouds():
            if cloud_id == cloud.cloud_id:
                continue

            other_cloud = AwsCloudDataHandler().get_aws_cloud(cloud_id)
            if other_cloud.access == "false":
                continue

            conn_name = "%s-to-%s" % (cloud.cloud_id, cloud_id)
            other_vpn_info = other_cloud.tunnel_vpn
            other_cascaded_info = other_cloud.cascaded_openstack
            other_vpn = VPN(public_ip=other_vpn_info["public_ip"],
                            user=VpnConstant.AWS_VPN_ROOT,
                            pass_word=VpnConstant.AWS_VPN_ROOT_PWD)

            logger.info("add conn on tunnel vpns...")
            vpn.add_tunnel(tunnel_name=conn_name,
                           left=vpn_info["public_ip"],
                           left_subnet=vpn_info["private_subnet"],
                           right=other_vpn_info["public_ip"],
                           right_subnet=other_vpn_info["private_subnet"])

            other_vpn.add_tunnel(tunnel_name=conn_name,
                                 left=other_vpn_info["public_ip"],
                                 left_subnet=other_vpn_info["private_subnet"],
                                 right=vpn_info["public_ip"],
                                 right_subnet=vpn_info["private_subnet"])

            vpn.restart_ipsec_service()
            other_vpn.restart_ipsec_service()

            # logger.info("add route on openstack cascadeds...")
            # cloud.cascaded add route
            # scp_file_to_host(host=cascaded_info["tunnel_ip"],
            #                  user=constant.Cascaded.ROOT,
            #                  password=constant.Cascaded.ROOT_PWD,
            #                  file_name=constant.Cascaded.ADD_ROUTE_SCRIPT,
            #                  local_dir=constant.Cascaded.SCRIPTS_DIR,
            #                  remote_dir=constant.Cascaded.REMOTE_SCRIPTS_DIR)
            #
            # execute_cmd_without_stdout(host=cascaded_info["tunnel_ip"],
            #                            user=constant.Cascaded.ROOT,
            #                            password=constant.Cascaded.ROOT_PWD,
            #                            cmd='cd %(dir)s; sh %(script)s %(subnet)s %(gw)s'
            #                                % {"dir": constant.Cascaded.REMOTE_SCRIPTS_DIR,
            #                                   "script": constant.Cascaded.ADD_ROUTE_SCRIPT,
            #                                   "subnet": other_vpn_info["private_subnet"],
            #                                   "gw": vpn_info["private_ip"]})

            # other_cloud.cascaded add route
            # scp_file_to_host(host=other_cascaded_info["tunnel_ip"],
            #                  user=constant.Cascaded.ROOT,
            #                  password=constant.Cascaded.ROOT_PWD,
            #                  file_name=constant.Cascaded.ADD_ROUTE_SCRIPT,
            #                  local_dir=constant.Cascaded.SCRIPTS_DIR,
            #                  remote_dir=constant.Cascaded.REMOTE_SCRIPTS_DIR)
            #
            # execute_cmd_without_stdout(host=other_cascaded_info["tunnel_ip"],
            #                            user=constant.Cascaded.ROOT,
            #                            password=constant.Cascaded.ROOT_PWD,
            #                            cmd='cd %(dir)s; sh %(script)s %(subnet)s %(gw)s'
            #                                % {"dir": constant.Cascaded.REMOTE_SCRIPTS_DIR,
            #                                   "script": constant.Cascaded.ADD_ROUTE_SCRIPT,
            #                                   "subnet": vpn_info["private_subnet"],
            #                                   "gw": other_vpn_info["private_ip"]})

            # add cloud-sg
            logger.info("add aws sg...")
            cascaded_installer.aws_cascaded_add_security(region=cloud.region,
                                                         az=cloud.az,
                                                         access_key_id=access_key_id,
                                                         secret_key=secret_key,
                                                         cidr="%s/32" % other_vpn_info["public_ip"])

            cascaded_installer.aws_cascaded_add_security(region=other_cloud.region,
                                                         az=other_cloud.az,
                                                         access_key_id=access_key_id,
                                                         secret_key=secret_key,
                                                         cidr="%s/32" % vpn_info["public_ip"])
        return True



    def list_aws_cloud(self):
        return AwsCloudDataHandler().list_aws_clouds()

    def get_aws_cloud(self, cloud_id):
        return AwsCloudDataHandler().get_aws_cloud(cloud_id)

    def delete_aws_cloud(self, region_name, az_alias):
        try:
            env_info = read_environment_info()
        except ReadEnvironmentInfoFailure as e:
            logger.error("read environment info error. check the config file.")
            return False

        cloud_id = self.__distribute_cloud_domain__(region_name=region_name, az_alias=az_alias, az_tag="--aws")

        aws_cloud_info = AwsCloudDataHandler().get_aws_cloud(cloud_id=cloud_id)

        cascaded_installer.aws_cascaded_uninstall(region=aws_cloud_info.region, az=aws_cloud_info.az,
                                                  access_key_id=aws_cloud_info.access_key_id,
                                                  secret_key=aws_cloud_info.secret_key)

        # config cacading
        try:
            execute_cmd_without_stdout(host=env_info["cascading_ip"],
                                       user=constant.Cascading.ROOT,
                                       password=constant.Cascading.ROOT_PWD,
                                       cmd='cd %(dir)s; sh %(script)s %(cascaded_domain)s'
                                           % {"dir": constant.RemoteConstant.REMOTE_SCRIPTS_DIR,
                                              "script": constant.RemoteConstant.REMOVE_AGGREGATE_SCRIPT,
                                              "cascaded_domain": aws_cloud_info.cascaded_openstack["cascaded_domain"]})
        except Exception as e:
            logger.error("remove aggregate error.")

        try:
            execute_cmd_without_stdout(host=env_info["cascading_ip"],
                                       user=constant.Cascading.ROOT,
                                       password=constant.Cascading.ROOT_PWD,
                                       cmd='cd %(dir)s; sh %(script)s %(cascaded_domain)s'
                                           % {"dir": constant.RemoteConstant.REMOTE_SCRIPTS_DIR,
                                              "script": constant.RemoteConstant.REMOVE_KEYSTONE_SCRIPT,
                                              "cascaded_domain": aws_cloud_info.cascaded_openstack["cascaded_domain"]})
        except Exception as e:
            logger.error("remove keystone endpoint error.")

        try:
            ProxyManager(env_info["cascading_ip"]).release_proxy(aws_cloud_info.proxy_info["host_name"])
            execute_cmd_without_stdout(host=env_info["cascading_ip"],
                                       user=constant.Cascading.ROOT, password=constant.Cascading.ROOT_PWD,
                                       cmd='cd %(dir)s; sh %(script)s %(proxy_host_name)s'
                                           % {"dir": constant.RemoteConstant.REMOTE_SCRIPTS_DIR,
                                              "script": constant.RemoteConstant.REMOVE_PROXY_SCRIPT,
                                              "proxy_host_name": aws_cloud_info.proxy_info["host_name"]})
        except Exception as e:
            logger.error("remove proxy error.")

        address = "/%(cascaded_domain)s/%(cascaded_ip)s"\
                  % {"cascaded_domain": aws_cloud_info.cascaded_openstack["cascaded_domain"],
                     "cascaded_ip": aws_cloud_info.cascaded_openstack["api_ip"]}

        try:
            execute_cmd_without_stdout(host=env_info["cascading_ip"],
                                       user=constant.Cascading.ROOT, password=constant.Cascading.ROOT_PWD,
                                       cmd='cd %(dir)s; sh %(script)s remove %(address)s'
                                           % {"dir": constant.Cascading.REMOTE_SCRIPTS_DIR,
                                              "script": constant.PublicConstant.MODIFY_DNS_SERVER_ADDRESS,
                                              "address": address})
        except Exception as e:
            logger.error("remove dns address error.")

        # config local_vpn
        try:
            local_vpn = VPN(env_info["vpn_ip"], constant.VpnConstant.VPN_ROOT, constant.VpnConstant.VPN_ROOT_PWD)
            local_vpn.remove_tunnel(aws_cloud_info.api_vpn["conn_name"])
            local_vpn.remove_tunnel(aws_cloud_info.tunnel_vpn["conn_name"])
        except Exception as e:
            logger.error("remove conn error.")

        # release subnet
        try:
            subnet_pair = {'api_subnet': aws_cloud_info.api_vpn["private_subnet"],
                           'tunnel_subnet': aws_cloud_info.tunnel_vpn["private_subnet"]}
            SubnetManager().release_subnet_pair(subnet_pair)
        except Exception as e:
            logger.error("release subnet error.")

        AwsCloudDataHandler().delete_aws_cloud(cloud_id)

        logger.info("delete cloud success. cloud_id = %s" % cloud_id)

        return True

    def update_remote_cloud(self):
        pass

