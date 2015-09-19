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
        logger.info("add cloud, cloud_type=%s, region_name=%s, az=%s, az_alias=%s, access=%s"
                    % (cloud_type, region_name, az, az_alias, access))
        try:
            env_info = read_environment_info()
        except ReadEnvironmentInfoFailure as e:
            logger.error("read environment info error. check the config file: %s", e.message)
            return False

        if cloud_type == "AWS":
            # distribute cloud_domain && proxy_name && vpn_subnet && hn_subnet for this cloud
            cascaded_domain = self.__distribute_cloud_domain__(region_name=region_name,
                                                               az_alias=az_alias,
                                                               az_tag="--aws")

            proxy_info = ProxyManager(env_info["cascading_ip"]).next_proxy_name()

            vpn_subnets = SubnetManager().distribute_subnet_pair()

            hn_subnet = self.__distribute_cidr_for_hn__()

            # install base environment
            aws_install_info = cascaded_installer.aws_cascaded_intall(region=get_region_id(region_name), az=az,
                                                                      access_key_id=access_key_id,
                                                                      secret_key=secret_key,
                                                                      api_cidr=vpn_subnets["api_subnet"],
                                                                      tunnel_cidr=vpn_subnets["tunnel_subnet"])
            # create a aws cloud instance.
            logger.info("install aws cascaded vm and vpn vm success.")
            cascaded_openstack = aws_install_info["cascaded_openstack"]
            cascaded_openstack["cascaded_domain"] = cascaded_domain

            api_vpn = aws_install_info["cascaded_apivpn"]
            api_vpn["private_subnet"] = vpn_subnets["api_subnet"]

            tunnel_vpn = aws_install_info["cascaded_tunnelvpn"]
            tunnel_vpn["private_subnet"] = vpn_subnets["tunnel_subnet"]

            cloud = awscloud.AwsCloud(cascaded_domain, get_region_id(region_name), az, access_key_id, secret_key,
                                      cascaded_openstack, api_vpn, tunnel_vpn, access=access.lower())

            # config local_vpn.
            logger.info("config local vpn ...")
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
            logger.info("wait aws vpn ...")
            self.__check_host_status__(host=api_vpn["public_ip"],
                                       user=constant.VpnConstant.AWS_VPN_ROOT,
                                       password=constant.VpnConstant.AWS_VPN_ROOT_PWD)

            self.__check_host_status__(host=tunnel_vpn["public_ip"],
                                       user=constant.VpnConstant.AWS_VPN_ROOT,
                                       password=constant.VpnConstant.AWS_VPN_ROOT_PWD)

            logger.info("config aws vpn ...")
            cloud.config_openstack_vpn(env_info["api_public_gw"], env_info["api_subnet"],
                                       env_info["tunnel_public_gw"], env_info["tunnel_subnet"])

            # add route to aws
            logger.info("add route to aws on cascading ...")
            try:
                self.__add_local_vpn_route__(host_ip=env_info["cascading_ip"],
                                             aws_api_subnet=api_vpn["private_subnet"],
                                             api_gw=env_info["api_vpn_ip"],
                                             aws_tunnel_subnet=tunnel_vpn["private_subnet"],
                                             tunnel_gw=env_info["tunnel_vpn_ip"])
            except Exception as e:
                logger.error("add route to aws on cascading error, %s" % e.message)

            logger.info("add route to aws on existed cascaded ...")
            for host in env_info["existed_cascaded"]:
                try:
                    self.__add_local_vpn_route__(host_ip=host,
                                                 aws_api_subnet=api_vpn["private_subnet"],
                                                 api_gw=env_info["api_vpn_ip"],
                                                 aws_tunnel_subnet=tunnel_vpn["private_subnet"],
                                                 tunnel_gw=env_info["tunnel_vpn_ip"])
                except Exception as e:
                    logger.error("add route to aws on existed cascaded error, error: %s" % e.message)

            # config proxy on cascading host
            if proxy_info is None:
                logger.info("wait proxy ...")
                proxy_info = self.__get_proxy_retry__(env_info["cascading_ip"])

            logger.info("add dhcp to proxy ...")
            cloud.proxy_info = proxy_info
            proxy_host_name = proxy_info["host_name"]
            proxy_num = proxy_info["proxy_num"]
            logger.debug("proxy_host_name = %s, proxy_num = %s" % (proxy_host_name, proxy_num))

            self.__config_proxy__(env_info["cascading_ip"], proxy_info)

            AwsCloudDataHandler().add_aws_cloud(cloud)

            # config cascading
            logger.info("config cascading ...")
            self.__config_cascading__(env_info, cascaded_openstack, aws_install_info["v2v_gateway"]["private_ip"])

            # config az_cascaded
            logger.info("wait cascaded ...")
            self.__check_host_status__(host=cascaded_openstack["tunnel_ip"],
                                       user=constant.Cascaded.ROOT,
                                       password=constant.Cascaded.ROOT_PWD)

            logger.info("config cascaded ...")
            self.__config_az_cascaded__(env_info, cascaded_openstack)

            logger.info("config patches config ...")
            self.__config_patch_tools__(cascading_ip=env_info["cascading_ip"], proxy_num=proxy_num,
                                        proxy_host_name=proxy_host_name,
                                        cascaded_domain=cascaded_domain,
                                        openstack_api_subnet=env_info["api_subnet"],
                                        aws_api_gw=api_vpn["private_ip"],
                                        openstack_tunnel_subnet=env_info["tunnel_subnet"],
                                        aws_tunnel_gw=tunnel_vpn["private_ip"],
                                        cascading_domain=env_info["cascading_domain"])

            self.__config_aws_patches__(env_info=env_info,
                                        cloud=cloud,
                                        aws_install_info=aws_install_info,
                                        hn_subnet=hn_subnet)

            logger.info("wait cascaded api ...")
            for i in range(3):
                try:
                    # check 120s
                    self.__check_host_status__(host=cascaded_openstack["api_ip"],
                                               user=constant.Cascaded.ROOT,
                                               password=constant.Cascaded.ROOT_PWD,
                                               retry_time=20, interval=1)
                    logger.info("cascaded api is ready..")
                    break
                except CheckHostStatusFailure as e:
                    if i == 2:
                        logger.error("check cascaded api failed ...")
                        break

                    logger.error("check cascaded api error, retry config cascaded ...")
                    self.__config_az_cascaded__(env_info, cascaded_openstack)

            self.__deploy_patches__(cascading_ip=env_info["cascading_ip"], cascaded_openstack=cascaded_openstack)

            if access.lower() == "true":
                try:
                    self.__enable_api_network_cross__(cloud=cloud,
                                                      access_key_id=access_key_id,
                                                      secret_key=secret_key)

                    self.__enable_tunnel_network_cross__(cloud=cloud,
                                                         access_key_id=access_key_id,
                                                         secret_key=secret_key)
                except Exception as e:
                    logger.error("enable network cross error: %s" % e.message)

            logger.info("success...")

            return True

        elif cloud_type == "vcloud":
            # add vmware cloud
            pass

    @staticmethod
    def __distribute_cloud_domain__(region_name, az_alias, az_tag):
        """distribute cloud domain
        :return:
        """
        domainpostfix = "huawei.com"
        l_region_name = region_name.lower()
        domain = ".".join([az_alias, l_region_name + az_tag, domainpostfix])
        return domain

    @staticmethod
    def __distribute_cidr_for_hn__():
        return {"cidr_vms": "172.29.252.0/24", "cidr_hns": "172.29.251.0/24"}

    @staticmethod
    def __check_host_status__(host, user, password, retry_time=100, interval=1):
        for i in range(retry_time):
            if check_ssh_server(host=host, user=user, password=password):
                return True
            else:
                time.sleep(interval)
        logger.error("check host status error, host = % s" % host)
        raise CheckHostStatusFailure(reason="check host status error, host = % s" % host)

    @staticmethod
    def __add_local_vpn_route__(host_ip, aws_api_subnet, api_gw, aws_tunnel_subnet, tunnel_gw):

        scp_file_to_host(host=host_ip, user=constant.Cascading.ROOT, password=constant.Cascading.ROOT_PWD,
                         file_name=constant.Cascading.ADD_VPN_ROUTE_SCRIPT,
                         local_dir=constant.Cascading.SCRIPTS_DIR,
                         remote_dir=constant.Cascading.REMOTE_SCRIPTS_DIR)

        execute_cmd_without_stdout(host=host_ip,
                                   user=constant.Cascading.ROOT, password=constant.Cascading.ROOT_PWD,
                                   cmd='cd %(dir)s; sh %(script)s '
                                       '%(aws_api_subnet)s %(api_gw)s %(aws_tunnel_subnet)s %(tunnel_gw)s'
                                       % {"dir": constant.Cascading.REMOTE_SCRIPTS_DIR,
                                          "script": constant.Cascading.ADD_VPN_ROUTE_SCRIPT,
                                          "aws_api_subnet": aws_api_subnet, "api_gw": api_gw,
                                          "aws_tunnel_subnet": aws_tunnel_subnet, "tunnel_gw": tunnel_gw})
        return True

    @staticmethod
    def __get_proxy_retry__(cascading_ip):
        logger.info("get proxy retry ...")
        proxy_info = ProxyManager(cascading_ip).next_proxy_name();
        for i in range(10):
            if proxy_info is None:
                time.sleep(20)
                proxy_info = ProxyManager().next_proxy_name();
            else:
                return proxy_info
        raise ConfigProxyFailure(reason="check proxy config result failed")

    @staticmethod
    def __config_proxy__(cascading_ip, proxy_info):
        logger.info("command role host add...")
        execute_cmd_without_stdout(host=cascading_ip, user=constant.Cascading.ROOT,
                                   password=constant.Cascading.ROOT_PWD,
                                   cmd="cps role-host-add --host %(proxy_host_name)s dhcp; cps commit"
                                       % {"proxy_host_name": proxy_info["host_name"]})
        return True

    @staticmethod
    def __config_az_cascaded__(env_info, cascaded_openstack):
        logger.info("start config cascaded host ...")
        cascaded_ip = cascaded_openstack["tunnel_ip"]
        # execute_cmd_without_stdout(host=cascaded_ip, user=constant.Cascaded.ROOT, password=constant.Cascaded.ROOT_PWD,
        #                            cmd='mkdir -p %(dir)s' % {"dir": constant.Cascaded.REMOTE_SCRIPTS_DIR})

        # modify dns server address
        # address = "/%(cascading_domain)s/%(cascading_ip)s,/%(cascaded_domain)s/%(cascaded_ip)s" \
        #           % {"cascading_domain": env_info["cascading_domain"],
        #              "cascading_ip": env_info["cascading_ip"],
        #              "cascaded_domain": cascaded_openstack["cascaded_domain"],
        #              "cascaded_ip": cascaded_openstack["api_ip"]}
        #
        # for i in range(30):
        #     try:
        #         scp_file_to_host(host=cascaded_ip,
        #                          user=constant.Cascaded.ROOT,
        #                          password=constant.Cascaded.ROOT_PWD,
        #                          file_name=constant.PublicConstant.MODIFY_DNS_SERVER_ADDRESS,
        #                          local_dir=constant.PublicConstant.SCRIPTS_DIR,
        #                          remote_dir=constant.Cascaded.REMOTE_SCRIPTS_DIR)
        #         time.sleep(5)
        #         break
        #     except SSHCommandFailure as e:
        #         logger.error("copy file error: %s" % e.format_message())
        #         time.sleep(5)
        #
        # for i in range(30):
        #     try:
        #         execute_cmd_without_stdout(host=cascaded_ip,
        #                                    user=constant.Cascaded.ROOT,
        #                                    password=constant.Cascaded.ROOT_PWD,
        #                                    cmd='cd %(dir)s; sh %(script)s replace %(address)s'
        #                                        % {"dir": constant.Cascaded.REMOTE_SCRIPTS_DIR,
        #                                           "script": constant.PublicConstant.MODIFY_DNS_SERVER_ADDRESS,
        #                                           "address": address})
        #         time.sleep(5)
        #         break
        #     except SSHCommandFailure as e:
        #         logger.error("modify cascaded dns address error: %s" % e.format_message())
        #         time.sleep(5)

        # # modify apach proxy on cascaded
        # gateway = self.__get_gateway__(cascaded_openstack["api_ip"])
        # for i in range(30):
        #     try:
        #         scp_file_to_host(host=cascaded_ip,
        #                          user=constant.Cascaded.ROOT,
        #                          password=constant.Cascaded.ROOT_PWD,
        #                          file_name=constant.Cascaded.MODIFY_PROXY_SCRIPT,
        #                          local_dir=constant.Cascaded.SCRIPTS_DIR,
        #                          remote_dir=constant.Cascaded.REMOTE_SCRIPTS_DIR)
        #         time.sleep(5)
        #         break
        #     except SSHCommandFailure as e:
        #         logger.error("copy file error: %s" % e.format_message())
        #         time.sleep(5)
        #
        # for i in range(30):
        #     try:
        #         execute_cmd_without_stdout(host=cascaded_ip, user=constant.Cascaded.ROOT,
        #                                    password=constant.Cascaded.ROOT_PWD,
        #                                    cmd='cd %(dir)s; sh %(script)s %(cascaded_ip)s %(cascaded_gw)s'
        #                                        % {"dir": constant.Cascaded.REMOTE_SCRIPTS_DIR,
        #                                           "script": constant.Cascaded.MODIFY_PROXY_SCRIPT,
        #                                           "cascaded_ip": cascaded_openstack["api_ip"],
        #                                           "cascaded_gw": gateway})
        #         time.sleep(5)
        #         break
        #     except SSHCommandFailure as e:
        #         logger.error("modify cascaded proxy error: %s" % e.format_message())
        #         time.sleep(5)

        # config cascaded domain
        # for i in range(30):
        #     try:
        #         scp_file_to_host(host=cascaded_ip,
        #                          user=constant.Cascaded.ROOT,
        #                          password=constant.Cascaded.ROOT_PWD,
        #                          file_name=constant.Cascaded.MODIFY_CASCADED_SCRIPT,
        #                          local_dir=constant.Cascaded.SCRIPTS_DIR,
        #                          remote_dir=constant.Cascaded.REMOTE_SCRIPTS_DIR)
        #         time.sleep(5)
        #         break
        #     except SSHCommandFailure as e:
        #         logger.error("copy file error: %s" % e.format_message())
        #         time.sleep(5)
        #
        # for i in range(30):
        #     try:
        #         execute_cmd_without_stdout(host=cascaded_ip, user=constant.Cascaded.ROOT,
        #                                    password=constant.Cascaded.ROOT_PWD,
        #                                    cmd='cd %(dir)s; sh %(script)s %(cascading_domain)s %(cascaded_domain)s'
        #                                        % {"dir": constant.Cascaded.REMOTE_SCRIPTS_DIR,
        #                                           "script": constant.Cascaded.MODIFY_CASCADED_SCRIPT,
        #                                           "cascading_domain": env_info["cascading_domain"],
        #                                           "cascaded_domain": cascaded_openstack["cascaded_domain"]})
        #         time.sleep(5)
        #         break
        #     except SSHCommandFailure as e:
        #         logger.error("modify cascaded domain error: %s" % e.format_message())
        #         time.sleep(5)

        # for i in range(30):
        #     try:
        #         scp_file_to_host(host=cascaded_ip,
        #                          user=constant.Cascaded.ROOT,
        #                          password=constant.Cascaded.ROOT_PWD,
        #                          file_name=constant.Cascaded.MODIFY_CASCADED_SCRIPT_PY,
        #                          local_dir=constant.Cascaded.SCRIPTS_DIR,
        #                          remote_dir=constant.Cascaded.REMOTE_SCRIPTS_DIR)
        #         time.sleep(5)
        #         break
        #     except SSHCommandFailure as e:
        #         logger.error("copy file error: %s" % e.format_message())
        #         time.sleep(5)

        gateway = __get_gateway__(cascaded_openstack["api_ip"])
        for i in range(30):
            try:
                execute_cmd_without_stdout(host=cascaded_ip, user=constant.Cascaded.ROOT,
                                           password=constant.Cascaded.ROOT_PWD,
                                           cmd='cd %(dir)s; python %(script)s '
                                               '%(cascading_domain)s %(cascading_ip)s '
                                               '%(cascaded_domain)s %(cascaded_ip)s '
                                               '%(gateway)s'
                                               % {"dir": constant.Cascaded.REMOTE_SCRIPTS_DIR,
                                                  "script": constant.Cascaded.MODIFY_CASCADED_SCRIPT_PY,
                                                  "cascading_domain": env_info["cascading_domain"],
                                                  "cascading_ip": env_info["cascading_ip"],
                                                  "cascaded_domain": cascaded_openstack["cascaded_domain"],
                                                  "cascaded_ip": cascaded_openstack["api_ip"],
                                                  "gateway": gateway})
                break
            except SSHCommandFailure as e:
                logger.error("modify cascaded domain error: %s" % e.format_message())
                time.sleep(5)


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

    @staticmethod
    def __config_cascading__(env_info, cascaded_openstack, v2v_gw):
        # config on cascading
        cascading_ip = env_info["cascading_ip"]
        # execute_cmd_without_stdout(host=cascading_ip, user=constant.Cascading.ROOT,password=constant.Cascading.ROOT_PWD,
        #                            cmd='mkdir -p %(dir)s' % {"dir": constant.Cascading.REMOTE_SCRIPTS_DIR})

        # modify dns server address
        address = "/%(cascaded_domain)s/%(cascaded_ip)s" \
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
                time.sleep(1)

        # config keystone
        # scp_file_to_host(host=cascading_ip, user=constant.Cascading.ROOT, password=constant.Cascading.ROOT_PWD,
        #                  file_name=constant.Cascading.KEYSTONE_ENDPOINT_SCRIPT,
        #                  local_dir=constant.Cascading.SCRIPTS_DIR,
        #                  remote_dir=constant.Cascading.REMOTE_SCRIPTS_DIR)

        for i in range(3):
            try:
                execute_cmd_without_stdout(host=cascading_ip, user=constant.Cascading.ROOT,
                                           password=constant.Cascading.ROOT_PWD,
                                           cmd='. %(env)s; cd %(dir)s; sh %(script)s %(cascaded_domain)s %(v2v_gw)s'
                                               % {"env": env_info["env"], "dir": constant.Cascading.REMOTE_SCRIPTS_DIR,
                                                  "script": constant.Cascading.KEYSTONE_ENDPOINT_SCRIPT,
                                                  "cascaded_domain": cascaded_openstack["cascaded_domain"],
                                                  "v2v_gw": v2v_gw})
                break
            except SSHCommandFailure as e:
                logger.error("create keystone endpoint error: %s" % e.format_message())
                time.sleep(1)

        logger.info("enable openstack service, cascading: %s" % cascading_ip)
        for i in range(3):
            try:
                execute_cmd_without_stdout(
                    host=cascading_ip,
                    user=constant.Cascading.ROOT,
                    password=constant.Cascading.ROOT_PWD,
                    cmd='cd %(dir)s; sh %(script)s %(cascaded_domain)s'
                        % {"dir": constant.Cascading.REMOTE_SCRIPTS_DIR,
                           "script": constant.Cascading.ENABLE_OPENSTACK_SERVICE,
                           "cascaded_domain": cascaded_openstack["cascaded_domain"]})
                break
            except Exception as e:
                logger.error("enable openstack service error, cascaded: %s, error: %s"
                             % (cascaded_openstack["cascaded_domain"], e.message))
                time.sleep(1)

        logger.info("enable openstack service success, cascading: %s" % cascading_ip)

        return True

    @staticmethod
    def __config_patch_tools__(cascading_ip, proxy_num, proxy_host_name, cascaded_domain,
                               openstack_api_subnet, aws_api_gw,
                               openstack_tunnel_subnet, aws_tunnel_gw, cascading_domain):
        execute_cmd_without_stdout(host=cascading_ip, user=constant.Cascading.ROOT,
                                   password=constant.Cascading.ROOT_PWD,
                                   cmd='cd %(dis)s; sh %(script)s '
                                       '%(proxy_num)s %(proxy_host_name)s %(cascaded_domain)s '
                                       '%(openstack_api_subnet)s %(aws_api_gw)s '
                                       '%(openstack_tunnel_subnet)s %(aws_tunnel_gw)s %(cascading_domain)s'
                                       % {"dis": constant.PatchesConstant.REMOTE_SCRIPTS_DIR,
                                          "script": constant.PatchesConstant.CONFIG_PATCHES_SCRIPT,
                                          "proxy_num": proxy_num, "proxy_host_name": proxy_host_name,
                                          "cascaded_domain": cascaded_domain,
                                          "openstack_api_subnet": openstack_api_subnet, "aws_api_gw": aws_api_gw,
                                          "openstack_tunnel_subnet": openstack_tunnel_subnet,
                                          "aws_tunnel_gw": aws_tunnel_gw, "cascading_domain": cascading_domain})
        return True

    @staticmethod
    def __config_aws_patches__(env_info, cloud, aws_install_info, hn_subnet):
        cascading_ip = env_info["cascading_ip"]
        openstack_api_subnet = env_info["api_subnet"]
        aws_api_gw = cloud.api_vpn["private_ip"]
        openstack_tunnel_subnet = env_info["tunnel_subnet"]
        aws_tunnel_gw = cloud.tunnel_vpn["private_ip"]
        cascaded_ip = cloud.cascaded_openstack["api_ip"]
        region = cloud.region
        az = cloud.az
        access_key_id = cloud.access_key_id
        secret_key = cloud.secret_key
        api_subnet_id = aws_install_info["subnet_info"]["api_subnet"]
        tunnel_subnet_id = aws_install_info["subnet_info"]["tunnel_subnet"]
        hynode_ami_id = aws_install_info["hynode_ami_id"]
        vpc_id = aws_install_info["vpc_id"]
        dns = "8.8.8.8"
        cgw_id = aws_install_info["v2v_gateway"]["vm_id"]
        cgw_ip = aws_install_info["v2v_gateway"]["private_ip"]
        internal_base_subnet_id = aws_install_info["subnet_info"]["base_subnet"]
        internal_base_ip = aws_install_info["cascaded_openstack"]["base_ip"]
        cascading_domain = env_info["cascading_domain"]

        execute_cmd_without_stdout(host=cascading_ip, user=constant.Cascading.ROOT,
                                   password=constant.Cascading.ROOT_PWD,
                                   cmd='cd /root/cloud_manager/patches; '
                                       'sh config_aws.sh %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s'
                                       % (dns, access_key_id, secret_key, region, az,
                                          api_subnet_id, tunnel_subnet_id, cgw_id, cgw_ip, cascaded_ip,
                                          openstack_api_subnet, aws_api_gw,
                                          openstack_tunnel_subnet, aws_tunnel_gw,
                                          hn_subnet["cidr_vms"], hn_subnet["cidr_hns"],
                                          internal_base_subnet_id,
                                          hynode_ami_id, vpc_id,
                                          internal_base_ip,
                                          cascading_domain))

        execute_cmd_without_stdout(host=cascading_ip, user=constant.Cascading.ROOT,
                                   password=constant.Cascading.ROOT_PWD,
                                   cmd='cd /root/cloud_manager/patches; sh config_add_route.sh %s %s %s %s'
                                       % (openstack_api_subnet, aws_api_gw,
                                          openstack_tunnel_subnet, aws_tunnel_gw))
        return True

    @staticmethod
    def __deploy_patches__(cascading_ip, cascaded_openstack):
        time.sleep(5)
        execute_cmd_without_stdout(host=cascading_ip, user=constant.Cascading.ROOT,
                                   password=constant.Cascading.ROOT_PWD,
                                   cmd='cd /root/cloud_manager/patches/patches_tool; python config.py cascading')

        time.sleep(5)
        execute_cmd_without_stdout(host=cascading_ip, user=constant.Cascading.ROOT,
                                   password=constant.Cascading.ROOT_PWD,
                                   cmd='cd /root/cloud_manager/patches/patches_tool; python config.py prepare')

        time.sleep(5)
        execute_cmd_without_stdout(host=cascading_ip, user=constant.Cascading.ROOT,
                                   password=constant.Cascading.ROOT_PWD,
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

    @staticmethod
    def __enable_api_network_cross__(cloud, access_key_id, secret_key):
        vpn_info = cloud.api_vpn
        cascaded_info = cloud.cascaded_openstack
        vpn = VPN(public_ip=vpn_info["public_ip"],
                  user=VpnConstant.AWS_VPN_ROOT,
                  pass_word=VpnConstant.AWS_VPN_ROOT_PWD)

        for other_cloud_id in AwsCloudDataHandler().list_aws_clouds():
            if other_cloud_id == cloud.cloud_id:
                continue

            other_cloud = AwsCloudDataHandler().get_aws_cloud(other_cloud_id)
            if other_cloud.access == "false":
                continue

            conn_name = "%s-api-%s" % (cloud.cloud_id, other_cloud_id)
            other_vpn_info = other_cloud.api_vpn
            other_cascaded_info = other_cloud.cascaded_openstack
            other_vpn = VPN(public_ip=other_vpn_info["public_ip"],
                            user=VpnConstant.AWS_VPN_ROOT,
                            pass_word=VpnConstant.AWS_VPN_ROOT_PWD)

            logger.info("add conn on api vpns...")
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

            logger.info("add route on openstack cascadeds...")
            # cloud.cascaded add route
            scp_file_to_host(host=cascaded_info["tunnel_ip"],
                             user=constant.Cascaded.ROOT,
                             password=constant.Cascaded.ROOT_PWD,
                             file_name=constant.Cascaded.ADD_API_ROUTE_SCRIPT,
                             local_dir=constant.Cascaded.SCRIPTS_DIR,
                             remote_dir=constant.Cascaded.REMOTE_SCRIPTS_DIR)

            execute_cmd_without_stdout(host=cascaded_info["tunnel_ip"],
                                       user=constant.Cascaded.ROOT,
                                       password=constant.Cascaded.ROOT_PWD,
                                       cmd='cd %(dir)s; sh %(script)s %(subnet)s %(gw)s'
                                           % {"dir": constant.Cascaded.REMOTE_SCRIPTS_DIR,
                                              "script": constant.Cascaded.ADD_API_ROUTE_SCRIPT,
                                              "subnet": other_vpn_info["private_subnet"],
                                              "gw": vpn_info["private_ip"]})

            # other_cloud.cascaded add route
            scp_file_to_host(host=other_cascaded_info["tunnel_ip"],
                             user=constant.Cascaded.ROOT,
                             password=constant.Cascaded.ROOT_PWD,
                             file_name=constant.Cascaded.ADD_API_ROUTE_SCRIPT,
                             local_dir=constant.Cascaded.SCRIPTS_DIR,
                             remote_dir=constant.Cascaded.REMOTE_SCRIPTS_DIR)

            execute_cmd_without_stdout(host=other_cascaded_info["tunnel_ip"],
                                       user=constant.Cascaded.ROOT,
                                       password=constant.Cascaded.ROOT_PWD,
                                       cmd='cd %(dir)s; sh %(script)s %(subnet)s %(gw)s'
                                           % {"dir": constant.Cascaded.REMOTE_SCRIPTS_DIR,
                                              "script": constant.Cascaded.ADD_API_ROUTE_SCRIPT,
                                              "subnet": vpn_info["private_subnet"],
                                              "gw": other_vpn_info["private_ip"]})

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

    @staticmethod
    def __enable_tunnel_network_cross__(cloud, access_key_id, secret_key):
        vpn_info = cloud.tunnel_vpn
        cascaded_info = cloud.cascaded_openstack
        vpn = VPN(public_ip=vpn_info["public_ip"],
                  user=VpnConstant.AWS_VPN_ROOT,
                  pass_word=VpnConstant.AWS_VPN_ROOT_PWD)

        for other_cloud_id in AwsCloudDataHandler().list_aws_clouds():
            if other_cloud_id == cloud.cloud_id:
                continue

            other_cloud = AwsCloudDataHandler().get_aws_cloud(other_cloud_id)
            if other_cloud.access == "false":
                continue

            conn_name = "%s-tunnel-%s" % (cloud.cloud_id, other_cloud_id)
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

    @staticmethod
    def __disable_network_cross__(cloud, access_key_id, secret_key):
        # only disable other_cloud vpn
        for other_cloud_id in AwsCloudDataHandler().list_aws_clouds():
            if other_cloud_id == cloud.cloud_id:
                continue

            other_cloud = AwsCloudDataHandler().get_aws_cloud(other_cloud_id)
            if other_cloud.access == "false":
                continue

            # delete api cross
            api_conn_name = "%s-api-%s" % (cloud.cloud_id, other_cloud.cloud_id)
            api_conn_name_alter = "%s-api-%s" % (other_cloud.cloud_id, cloud.cloud_id)
            other_api_vpn_info = other_cloud.api_vpn
            other_api_vpn = VPN(public_ip=other_api_vpn_info["public_ip"],
                                user=VpnConstant.AWS_VPN_ROOT,
                                pass_word=VpnConstant.AWS_VPN_ROOT_PWD)

            logger.info("remove conn on api vpn...")

            other_api_vpn.remove_tunnel(api_conn_name)

            other_api_vpn.remove_tunnel(api_conn_name_alter)

            other_api_vpn.restart_ipsec_service()


            # delete tunnel cross
            tunnel_conn_name = "%s-tunnel-%s" % (cloud.cloud_id, other_cloud.cloud_id)
            tunnel_conn_name_alter = "%s-tunnel-%s" % (other_cloud.cloud_id, cloud.cloud_id)
            other_tunnel_vpn_info = other_cloud.tunnel_vpn
            other_tunnel_vpn = VPN(public_ip=other_tunnel_vpn_info["public_ip"],
                                   user=VpnConstant.AWS_VPN_ROOT,
                                   pass_word=VpnConstant.AWS_VPN_ROOT_PWD)

            logger.info("remove conn on tunnel vpn...")

            other_tunnel_vpn.remove_tunnel(tunnel_conn_name)

            other_tunnel_vpn.remove_tunnel(tunnel_conn_name_alter)

            other_tunnel_vpn.restart_ipsec_service()

            # remove cloud-sg
            logger.info("remove aws sg...")
            try:
                cascaded_installer.aws_cascaded_remove_security(region=other_cloud.region,
                                                                az=other_cloud.az,
                                                                access_key_id=access_key_id,
                                                                secret_key=secret_key,
                                                                cidr="%s/32" % cloud.api_vpn["public_ip"])
            except Exception as e:
                logger.error("remove aws api sg error, region: %s, error: %s" % (other_cloud.region, e.message))

            try:
                cascaded_installer.aws_cascaded_remove_security(region=other_cloud.region,
                                                                az=other_cloud.az,
                                                                access_key_id=access_key_id,
                                                                secret_key=secret_key,
                                                                cidr="%s/32" % cloud.tunnel_vpn["public_ip"])
            except Exception as e:
                logger.error("remove aws tunnel sg error, error: %s" % e.message)

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
                                           % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                                              "script": constant.RemoveConstant.REMOVE_AGGREGATE_SCRIPT,
                                              "cascaded_domain": aws_cloud_info.cascaded_openstack["cascaded_domain"]})
        except Exception as e:
            logger.error("remove aggregate error, error: %s" % e.message)

        try:
            execute_cmd_without_stdout(host=env_info["cascading_ip"],
                                       user=constant.Cascading.ROOT,
                                       password=constant.Cascading.ROOT_PWD,
                                       cmd='cd %(dir)s; sh %(script)s %(cascaded_domain)s'
                                           % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                                              "script": constant.RemoveConstant.REMOVE_CINDER_SERVICE_SCRIPT,
                                              "cascaded_domain": aws_cloud_info.cascaded_openstack["cascaded_domain"]})
        except Exception as e:
            logger.error("remove cinder service error, error: %s" % e.message)

        try:
            execute_cmd_without_stdout(host=env_info["cascading_ip"],
                                       user=constant.Cascading.ROOT,
                                       password=constant.Cascading.ROOT_PWD,
                                       cmd='cd %(dir)s; sh %(script)s %(cascaded_domain)s'
                                           % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                                              "script": constant.RemoveConstant.REMOVE_NEUTRON_AGENT_SCRIPT,
                                              "cascaded_domain": aws_cloud_info.cascaded_openstack["cascaded_domain"]})

            execute_cmd_without_stdout(host=env_info["cascading_ip"],
                                       user=constant.Cascading.ROOT,
                                       password=constant.Cascading.ROOT_PWD,
                                       cmd='cd %(dir)s; sh %(script)s %(proxy_host)s'
                                           % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                                              "script": constant.RemoveConstant.REMOVE_NEUTRON_AGENT_SCRIPT,
                                              "proxy_host": aws_cloud_info.proxy_info["host_name"]})

        except Exception as e:
            logger.error("remove neutron agent error, error: %s" % e.message)

        try:
            execute_cmd_without_stdout(host=env_info["cascading_ip"],
                                       user=constant.Cascading.ROOT,
                                       password=constant.Cascading.ROOT_PWD,
                                       cmd='cd %(dir)s; sh %(script)s %(cascaded_domain)s'
                                           % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                                              "script": constant.RemoveConstant.REMOVE_KEYSTONE_SCRIPT,
                                              "cascaded_domain": aws_cloud_info.cascaded_openstack["cascaded_domain"]})
        except Exception as e:
            logger.error("remove keystone endpoint error.")

        try:
            ProxyManager(env_info["cascading_ip"]).release_proxy(aws_cloud_info.proxy_info["host_name"])
            execute_cmd_without_stdout(host=env_info["cascading_ip"],
                                       user=constant.Cascading.ROOT, password=constant.Cascading.ROOT_PWD,
                                       cmd='cd %(dir)s; sh %(script)s %(proxy_host_name)s'
                                           % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                                              "script": constant.RemoveConstant.REMOVE_PROXY_SCRIPT,
                                              "proxy_host_name": aws_cloud_info.proxy_info["host_name"]})
        except Exception as e:
            logger.error("remove proxy error.")

        address = "/%(cascaded_domain)s/%(cascaded_ip)s" \
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

        self.__disable_network_cross__(aws_cloud_info,
                                       access_key_id=aws_cloud_info.access_key_id,
                                       secret_key=aws_cloud_info.secret_key)

        AwsCloudDataHandler().delete_aws_cloud(cloud_id)

        logger.info("delete cloud success. cloud_id = %s" % cloud_id)

        return True

    def update_remote_cloud(self):
        pass


def __get_gateway__(ip, mask=None):
    arr = ip.split(".")
    gateway = "%s.%s.%s.1" % (arr[0], arr[1], arr[2])
    return gateway


if __name__ == '__main__':
    pass
