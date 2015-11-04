# -*- coding:utf-8 -*-

__author__ = 'q00222219@huawei'

import threading

import constant
import awscloud
import install.cascaded_installer as cascaded_installer
from vpn import VPN
from commonutils import *
from environmentinfo import *
from awscloudpersist import AwsCloudDataHandler
# from proxy_manager import ProxyManager
import proxy_manager_ex as proxy_manager
from subnet_manager import SubnetManager
from region_mapping import *
from constant import *
from vpn_configer import VpnConfiger
from cascading_configer import CascadingConfiger
from cascaded_configer import CascadedConfiger
from hypernode_manager.hypernode_manager import HyperNodeManager

logger.init('CloudManager')


class CloudManager:
    def __init__(self):
        self.local_vpn_thread = None
        self.remote_api_vpn_thread = None
        self.remote_tunnel_vpn_thread = None
        self.cascading_thread = None
        self.cascaded_thread = None

    def add_remote_cloud(self, cloud_type, region_name, az, az_alias,
                         access_key_id, secret_key, access=True,
                         driver_type="agentless"):
        start_time = time.time()
        logger.info("start add cloud, cloud_type=%s, region_name=%s, "
                    "az=%s, az_alias=%s, access=%s, driver_type=%s"
                    % (cloud_type, region_name, az, az_alias,
                       access, driver_type))
        try:
            env_info = read_environment_info()
        except ReadEnvironmentInfoFailure as e:
            logger.error(
                "read environment info error. check the config file: %s"
                % e.message)
            return False

        if cloud_type == "AWS":
            # distribute cloud_domain && proxy_name for this cloud
            cascaded_domain = self._distribute_cloud_domain(
                region_name=region_name,
                az_alias=az_alias,
                az_tag="--aws")

            # proxy_info = \
            #     ProxyManager(env_info["cascading_ip"]).next_proxy_name()
            proxy_info = proxy_manager.distribute_proxy()

            # distribute vpn_subnet && hn_subnet for this cloud
            vpn_subnets = SubnetManager().distribute_subnet_pair()
            hn_subnet = self._distribute_cidr_for_hn()

            # install base environment
            aws_install_info = cascaded_installer.aws_cascaded_install(
                region=get_region_id(region_name),
                az=az,
                access_key_id=access_key_id,
                secret_key=secret_key,
                api_cidr=vpn_subnets["api_subnet"],
                tunnel_cidr=vpn_subnets["tunnel_subnet"],
                ceph_cidr=vpn_subnets["api_subnet"],
                public_gw=env_info["api_public_gw"],
                local_api_cidr=env_info["api_subnet"],
                local_tunnel_cidr=env_info["tunnel_subnet"])

            if aws_install_info is None:
                logger.error("install aws cascaded vm and vpn vm error.")
                return False

            logger.info("install aws cascaded vm and vpn vm success.")

            # create a aws cloud instance.
            cascaded_openstack = aws_install_info["cascaded_openstack"]
            cascaded_openstack["cascaded_domain"] = cascaded_domain

            api_vpn = aws_install_info["cascaded_apivpn"]
            api_vpn["private_subnet"] = vpn_subnets["api_subnet"]

            tunnel_vpn = aws_install_info["cascaded_tunnelvpn"]
            tunnel_vpn["private_subnet"] = vpn_subnets["tunnel_subnet"]

            cloud = awscloud.AwsCloud(cascaded_domain,
                                      get_region_id(region_name),
                                      az,
                                      access_key_id, secret_key,
                                      cascaded_openstack, api_vpn, tunnel_vpn,
                                      aws_install_info["vpc_id"],
                                      driver_type=driver_type,
                                      access=access,
                                      ceph_vm=aws_install_info["ceph_vm_info"])

            # config local_vpn.
            vpn_conn_name = cloud.get_vpn_conn_name()
            api_vpn["conn_name"] = vpn_conn_name["api_conn_name"]
            tunnel_vpn["conn_name"] = vpn_conn_name["tunnel_conn_name"]

            logger.info("config local vpn thread")
            local_vpn_cf = VpnConfiger(
                host_ip=env_info["vpn_ip"],
                user=constant.VpnConstant.VPN_ROOT,
                password=constant.VpnConstant.VPN_ROOT_PWD)

            local_vpn_cf.register_add_conns(
                tunnel_name=api_vpn["conn_name"],
                left_public_ip=env_info["api_public_gw"],
                left_subnet=env_info["api_subnet"],
                right_public_ip=cloud.api_vpn["public_ip"],
                right_subnet=cloud.api_vpn["private_subnet"])

            local_vpn_cf.register_add_conns(
                tunnel_name=tunnel_vpn["conn_name"],
                left_public_ip=env_info["tunnel_public_gw"],
                left_subnet=env_info["tunnel_subnet"],
                right_public_ip=cloud.tunnel_vpn["public_ip"],
                right_subnet=cloud.tunnel_vpn["private_subnet"])

            self.local_vpn_thread = threading.Thread(
                target=local_vpn_cf.do_config)

            logger.info("config remote api vpn thread")
            remote_api_vpn_cf = VpnConfiger(
                host_ip=api_vpn["public_ip"],
                user=constant.VpnConstant.AWS_VPN_ROOT,
                password=constant.VpnConstant.AWS_VPN_ROOT_PWD)

            remote_api_vpn_cf.register_add_conns(
                tunnel_name=api_vpn["conn_name"],
                left_public_ip=cloud.api_vpn["public_ip"],
                left_subnet=cloud.api_vpn["private_subnet"],
                right_public_ip=env_info["api_public_gw"],
                right_subnet=env_info["api_subnet"])

            self.remote_api_vpn_thread = threading.Thread(
                target=remote_api_vpn_cf.do_config)

            logger.info("config remote tunnel vpn thread")
            remote_tunnel_vpn_cf = VpnConfiger(
                host_ip=tunnel_vpn["public_ip"],
                user=constant.VpnConstant.AWS_VPN_ROOT,
                password=constant.VpnConstant.AWS_VPN_ROOT_PWD)

            remote_tunnel_vpn_cf.register_add_conns(
                tunnel_name=tunnel_vpn["conn_name"],
                left_public_ip=cloud.tunnel_vpn["public_ip"],
                left_subnet=cloud.tunnel_vpn["private_subnet"],
                right_public_ip=env_info["tunnel_public_gw"],
                right_subnet=env_info["tunnel_subnet"])

            self.remote_tunnel_vpn_thread = threading.Thread(
                target=remote_tunnel_vpn_cf.do_config)

            logger.info("config cascading thread")
            cascading_cf = CascadingConfiger(
                api_ip=env_info["cascading_ip"],
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cascaded_domain=cascaded_domain,
                cascaded_ip=cascaded_openstack["api_ip"],
                v2v_gw=aws_install_info["v2v_gateway"]["private_ip"])

            self.cascading_thread = threading.Thread(
                target=cascading_cf.do_config)

            logger.info("config cascaded thread")
            cascaded_cf = CascadedConfiger(
                api_ip=cascaded_openstack["api_ip"],
                tunnel_ip=cascaded_openstack["tunnel_ip"],
                domain=cascaded_domain,
                user=constant.Cascaded.ROOT,
                password=constant.Cascaded.ROOT_PWD,
                cascading_domain=env_info["cascading_domain"],
                cascading_ip=env_info["cascading_ip"])

            self.cascaded_thread = threading.Thread(
                target=cascaded_cf.do_config)

            cost_time = time.time() - start_time
            logger.info("start all thread, cost time: %d" % cost_time)
            self._start_all_threads()

            logger.info("add route to aws on cascading ...")
            self._add_vpn_route(
                host_ip=env_info["cascading_ip"],
                aws_api_subnet=api_vpn["private_subnet"],
                api_gw=env_info["api_vpn_ip"],
                aws_tunnel_subnet=tunnel_vpn["private_subnet"],
                tunnel_gw=env_info["tunnel_vpn_ip"])

            logger.info("add route to aws on existed cascaded ...")
            for host in env_info["existed_cascaded"]:
                self._add_vpn_route(
                    host_ip=host,
                    aws_api_subnet=api_vpn["private_subnet"],
                    api_gw=env_info["api_vpn_ip"],
                    aws_tunnel_subnet=tunnel_vpn["private_subnet"],
                    tunnel_gw=env_info["tunnel_vpn_ip"])

            # config proxy on cascading host
            if proxy_info is None:
                logger.info("wait proxy ...")
                proxy_info = self._get_proxy_retry(env_info["cascading_ip"])

            logger.info("add dhcp to proxy ...")
            cloud.proxy_info = proxy_info
            proxy_id = proxy_info["id"]
            proxy_num = proxy_info["proxy_num"]
            logger.debug("proxy_id = %s, proxy_num = %s"
                         % (proxy_id, proxy_num))

            self._config_proxy(env_info["cascading_ip"], proxy_info)

            AwsCloudDataHandler().add_aws_cloud(cloud)

            logger.info("config patches config ...")
            self._config_patch_tools(
                cascading_ip=env_info["cascading_ip"],
                proxy_num=proxy_num,
                proxy_host_name=proxy_id,
                cascaded_domain=cascaded_domain,
                openstack_api_subnet=env_info["api_subnet"],
                aws_api_gw=api_vpn["private_ip"],
                openstack_tunnel_subnet=env_info["tunnel_subnet"],
                aws_tunnel_gw=tunnel_vpn["private_ip"],
                cascading_domain=env_info["cascading_domain"])

            self._config_aws_patches(env_info=env_info,
                                     cloud=cloud,
                                     aws_install_info=aws_install_info,
                                     hn_subnet=hn_subnet,
                                     driver_type=driver_type)

            cost_time = time.time() - start_time
            logger.info("wait all thread success, cost time: %d" % cost_time)
            self._join_all_threads()

            cost_time = time.time() - start_time
            logger.info("config success, cost time: %d" % cost_time)
            self._deploy_patches(
                cascading_ip=env_info["cascading_ip"],
                cascaded_openstack=cascaded_openstack)

            logger.info("config storage...")
            ceph_vms = aws_install_info["ceph_vm_info"]
            self._config_storage(
                cascaded_ip=cascaded_openstack["api_ip"],
                user=constant.Cascaded.ROOT,
                password=constant.Cascaded.ROOT_PWD,
                cascading_domain=env_info["cascading_domain"],
                cascaded_domain=cascaded_domain,
                ceph_vms=ceph_vms)

            if access:
                try:
                    self._enable_api_network_cross(
                        cloud=cloud,
                        access_key_id=access_key_id,
                        secret_key=secret_key)

                    self._enable_tunnel_network_cross(
                        cloud=cloud,
                        access_key_id=access_key_id,
                        secret_key=secret_key)
                except Exception as e:
                    logger.error("enable network cross error: %s"
                                 % e.message)

            cost_time = time.time() - start_time
            logger.info("success, cost time: %d" % cost_time)

            return True

        elif cloud_type == "vcloud":
            # add vcloud
            pass

    def _start_all_threads(self):
        self.local_vpn_thread.start()
        self.remote_api_vpn_thread.start()
        self.remote_tunnel_vpn_thread.start()
        self.cascading_thread.start()
        self.cascaded_thread.start()

    def _join_all_threads(self):
        self.local_vpn_thread.join()
        self.remote_api_vpn_thread.join()
        self.remote_tunnel_vpn_thread.join()
        self.cascading_thread.join()
        self.cascaded_thread.join()

    @staticmethod
    def _distribute_cloud_domain(region_name, az_alias, az_tag):
        """distribute cloud domain
        :return:
        """
        domainpostfix = "huawei.com"
        l_region_name = region_name.lower()
        domain = ".".join([az_alias, l_region_name + az_tag, domainpostfix])
        return domain

    @staticmethod
    def _distribute_cidr_for_hn():
        return {"cidr_vms": "172.29.252.0/24", "cidr_hns": "172.29.251.0/24"}

    @staticmethod
    def _add_vpn_route(host_ip, aws_api_subnet, api_gw,
                       aws_tunnel_subnet, tunnel_gw):
        try:
            execute_cmd_without_stdout(
                host=host_ip,
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s '
                    '%(aws_api_subnet)s %(api_gw)s '
                    '%(aws_tunnel_subnet)s %(tunnel_gw)s'
                    % {"dir": constant.Cascading.REMOTE_SCRIPTS_DIR,
                       "script": constant.Cascading.ADD_VPN_ROUTE_SCRIPT,
                       "aws_api_subnet": aws_api_subnet, "api_gw": api_gw,
                       "aws_tunnel_subnet": aws_tunnel_subnet,
                       "tunnel_gw": tunnel_gw})
        except SSHCommandFailure:
            logger.error("add vpn route error, host: %s" % host_ip)
            return False
        return True

    @staticmethod
    def _get_proxy_retry(cascading_ip):
        logger.info("get proxy retry ...")
        # proxy_manager = ProxyManager(cascading_ip)
        # proxy_info = proxy_manager.next_proxy_name()
        proxy_info = proxy_manager.distribute_proxy()
        for i in range(10):
            if proxy_info is None:
                time.sleep(20)
                # proxy_info = proxy_manager.next_proxy_name()
                proxy_info = proxy_manager.distribute_proxy()
            else:
                return proxy_info
        raise ConfigProxyFailure(error="check proxy config result failed")

    @staticmethod
    def _config_proxy(cascading_ip, proxy_info):
        logger.info("command role host add...")
        for i in range(3):
            try:
                execute_cmd_without_stdout(
                    host=cascading_ip,
                    user=constant.Cascading.ROOT,
                    password=constant.Cascading.ROOT_PWD,
                    cmd="cps role-host-add --host %(proxy_host_name)s dhcp;"
                        "cps commit"
                        % {"proxy_host_name": proxy_info["id"]})
            except SSHCommandFailure:
                logger.error("config proxy error, try again...")
        return True

    @staticmethod
    def _config_patch_tools(cascading_ip, proxy_num, proxy_host_name,
                            cascaded_domain,
                            openstack_api_subnet, aws_api_gw,
                            openstack_tunnel_subnet, aws_tunnel_gw,
                            cascading_domain):
        for i in range(10):
            try:
                execute_cmd_without_stdout(
                    host=cascading_ip, user=constant.Cascading.ROOT,
                    password=constant.Cascading.ROOT_PWD,
                    cmd='cd %(dis)s; sh %(script)s '
                        '%(proxy_num)s %(proxy_host_name)s %(cascaded_domain)s '
                        '%(openstack_api_subnet)s %(aws_api_gw)s '
                        '%(openstack_tunnel_subnet)s %(aws_tunnel_gw)s '
                        '%(cascading_domain)s'
                        % {"dis": constant.PatchesConstant.REMOTE_SCRIPTS_DIR,
                           "script":
                               constant.PatchesConstant.CONFIG_PATCHES_SCRIPT,
                           "proxy_num": proxy_num,
                           "proxy_host_name": proxy_host_name,
                           "cascaded_domain": cascaded_domain,
                           "openstack_api_subnet": openstack_api_subnet,
                           "aws_api_gw": aws_api_gw,
                           "openstack_tunnel_subnet": openstack_tunnel_subnet,
                           "aws_tunnel_gw": aws_tunnel_gw,
                           "cascading_domain": cascading_domain})
                return True
            except Exception as e:
                logger.error("config patch tool error, error: %s"
                             % e.message)
                continue
        return True

    @staticmethod
    def _config_aws_patches(env_info, cloud, aws_install_info,
                            hn_subnet, driver_type):
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
        cgw_id = aws_install_info["v2v_gateway"]["vm_id"]
        cgw_ip = aws_install_info["v2v_gateway"]["private_ip"]
        internal_base_subnet_id = aws_install_info["subnet_info"]["base_subnet"]
        internal_base_ip = aws_install_info["cascaded_openstack"]["base_ip"]
        cascading_domain = env_info["cascading_domain"]

        for i in range(10):
            try:
                execute_cmd_without_stdout(
                    host=cascading_ip,
                    user=constant.Cascading.ROOT,
                    password=constant.Cascading.ROOT_PWD,
                    cmd='cd /root/cloud_manager/patches; '
                        'sh config_aws.sh %s %s %s %s %s %s %s %s %s '
                        '%s %s %s %s %s %s %s %s %s %s %s %s'
                        % (access_key_id, secret_key, region, az,
                           api_subnet_id, tunnel_subnet_id, cgw_id, cgw_ip,
                           cascaded_ip,
                           openstack_api_subnet, aws_api_gw,
                           openstack_tunnel_subnet, aws_tunnel_gw,
                           hn_subnet["cidr_vms"], hn_subnet["cidr_hns"],
                           internal_base_subnet_id,
                           hynode_ami_id, vpc_id,
                           internal_base_ip,
                           cascading_domain,
                           driver_type))
                break
            except Exception as e:
                logger.error("conf aws file error, error: %s" % e.message)
                continue

        for i in range(10):
            try:
                execute_cmd_without_stdout(
                    host=cascading_ip, user=constant.Cascading.ROOT,
                    password=constant.Cascading.ROOT_PWD,
                    cmd='cd /root/cloud_manager/patches;sh config_add_route.sh '
                        '%s %s %s %s'
                        % (openstack_api_subnet, aws_api_gw,
                           openstack_tunnel_subnet, aws_tunnel_gw))
                break
            except Exception as e:
                logger.error("conf route error, error: %s"
                             % e.message)
                continue
        return True

    @staticmethod
    def _deploy_patches(cascading_ip, cascaded_openstack):
        execute_cmd_without_stdout(
            host=cascading_ip,
            user=constant.Cascading.ROOT,
            password=constant.Cascading.ROOT_PWD,
            cmd='cd /root/cloud_manager/patches/patches_tool;'
                'python config.py cascading')

        execute_cmd_without_stdout(
            host=cascading_ip,
            user=constant.Cascading.ROOT,
            password=constant.Cascading.ROOT_PWD,
            cmd='cd /root/cloud_manager/patches/patches_tool;'
                'python config.py prepare')

        execute_cmd_without_stdout(
            host=cascading_ip,
            user=constant.Cascading.ROOT,
            password=constant.Cascading.ROOT_PWD,
            cmd='cd /root/cloud_manager/patches/patches_tool;'
                'python patches_tool.py')

        cascaded_ip = cascaded_openstack["tunnel_ip"]

        for i in range(3):
            try:
                execute_cmd_without_stdout(
                    host=cascaded_ip,
                    user=constant.Cascaded.ROOT,
                    password=constant.Cascaded.ROOT_PWD,
                    cmd='cd %(dir)s; python %(script)s aws_config.ini'
                        % {"dir": "/home/fsp/patches_tool/aws_patch",
                           "script": "patch_file.py"})
                break
            except SSHCommandFailure as e:
                logger.error("patch aws patch error: %s" % e.format_message())
                time.sleep(5)
                execute_cmd_without_stdout(
                    host=cascading_ip,
                    user=constant.Cascading.ROOT,
                    password=constant.Cascading.ROOT_PWD,
                    cmd='cd /root/cloud_manager/patches/patches_tool;'
                        'python config.py prepare')
                continue

        return True

    @staticmethod
    def _enable_api_network_cross(cloud, access_key_id, secret_key):
        vpn_info = cloud.api_vpn
        cascaded_info = cloud.cascaded_openstack
        vpn = VPN(public_ip=vpn_info["public_ip"],
                  user=VpnConstant.AWS_VPN_ROOT,
                  pass_word=VpnConstant.AWS_VPN_ROOT_PWD)

        for other_cloud_id in AwsCloudDataHandler().list_aws_clouds():
            if other_cloud_id == cloud.cloud_id:
                continue

            other_cloud = AwsCloudDataHandler().get_aws_cloud(other_cloud_id)
            if not other_cloud.access:
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
            # scp_file_to_host(host=cascaded_info["tunnel_ip"],
            #                  user=constant.Cascaded.ROOT,
            #                  password=constant.Cascaded.ROOT_PWD,
            #                  file_name=constant.Cascaded.ADD_API_ROUTE_SCRIPT,
            #                  local_dir=constant.Cascaded.SCRIPTS_DIR,
            #                  remote_dir=constant.Cascaded.REMOTE_SCRIPTS_DIR)

            execute_cmd_without_stdout(
                host=cascaded_info["tunnel_ip"],
                user=constant.Cascaded.ROOT,
                password=constant.Cascaded.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s %(subnet)s %(gw)s'
                    % {"dir": constant.Cascaded.REMOTE_SCRIPTS_DIR,
                       "script": constant.Cascaded.ADD_API_ROUTE_SCRIPT,
                       "subnet": other_vpn_info["private_subnet"],
                       "gw": vpn_info["private_ip"]})

            # other_cloud.cascaded add route
            # scp_file_to_host(host=other_cascaded_info["tunnel_ip"],
            #                  user=constant.Cascaded.ROOT,
            #                  password=constant.Cascaded.ROOT_PWD,
            #                  file_name=constant.Cascaded.ADD_API_ROUTE_SCRIPT,
            #                  local_dir=constant.Cascaded.SCRIPTS_DIR,
            #                  remote_dir=constant.Cascaded.REMOTE_SCRIPTS_DIR)

            execute_cmd_without_stdout(
                host=other_cascaded_info["tunnel_ip"],
                user=constant.Cascaded.ROOT,
                password=constant.Cascaded.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s %(subnet)s %(gw)s'
                    % {"dir": constant.Cascaded.REMOTE_SCRIPTS_DIR,
                       "script": constant.Cascaded.ADD_API_ROUTE_SCRIPT,
                       "subnet": vpn_info["private_subnet"],
                       "gw": other_vpn_info["private_ip"]})

            # add cloud-sg
            logger.info("add aws sg...")
            cascaded_installer.aws_cascaded_add_security(
                region=cloud.region,
                az=cloud.az,
                access_key_id=access_key_id,
                secret_key=secret_key,
                cidr="%s/32" % other_vpn_info["public_ip"])

            cascaded_installer.aws_cascaded_add_security(
                region=other_cloud.region,
                az=other_cloud.az,
                access_key_id=access_key_id,
                secret_key=secret_key,
                cidr="%s/32" % vpn_info["public_ip"])
        return True

    @staticmethod
    def _config_storage(cascaded_ip, user, password, cascading_domain,
                        cascaded_domain, ceph_vms):
        # 1. create env file and config cinder on cascaded host
        for i in range(7):
            try:
                execute_cmd_without_stdout(
                    host=cascaded_ip,
                    user=user,
                    password=password,
                    cmd='cd %(dir)s;'
                        'sh %(create_env_script)s %(cascading_domain)s '
                        '%(cascaded_domain)s;'
                        'sh %(conf_cinder_script)s '
                        '%(original_cascaded_domain)s '
                        '%(backup_cascaded_domain)s'
                        % {"dir": constant.Cascaded.REMOTE_SCRIPTS_DIR,
                           "create_env_script": constant.Cascaded.CREATE_ENV,
                           "cascading_domain": cascading_domain,
                           "cascaded_domain": cascaded_domain,
                           "conf_cinder_script":
                               constant.Cascaded.CONFIG_CINDER_SCRIPT,
                           "original_cascaded_domain": cascaded_domain,
                           "backup_cascaded_domain": cascaded_domain})
                break
            except Exception as e1:
                logger.error("modify env file and config cinder "
                             "on cascaded host error: %s"
                             % e1.message)
                time.sleep(1)
                continue

        # 2. config ceph nodes
        for i in range(7):
            try:
                execute_cmd_without_stdout(
                    host=ceph_vms["ceph_deploy_vm_ip"],
                    user=constant.CephConstant.USER,
                    password=constant.CephConstant.PWD,
                    cmd='/bin/bash %(ceph_install_script)s %(deploy_ip)s '
                        '%(node1_ip)s %(node2_ip)s %(node3_ip)s'
                        % {"ceph_install_script":
                               constant.CephConstant.CEPH_INSTALL_SCRIPT,
                           "deploy_ip": ceph_vms["ceph_deploy_vm_ip"],
                           "node1_ip": ceph_vms["ceph_node1_vm_ip"],
                           "node2_ip": ceph_vms["ceph_node2_vm_ip"],
                           "node3_ip": ceph_vms["ceph_node3_vm_ip"]})
                break
            except SSHCommandFailure as e2:
                logger.error("install ceph nodes error, error: %s" % e2.message)
                time.sleep(1)
                continue

        # 3. config cinder on cascaded host
        for i in range(7):
            try:
                execute_cmd_without_stdout(
                    host=cascaded_ip,
                    user=user,
                    password=password,
                    cmd='cd %(dir)s; python %(config_backup_script)s '
                        '--domain=%(cascaded_domain)s '
                        '--backup_domain=%(backup_cascaded_domain)s '
                        '--host=%(host_ip)s '
                        '--backup_host=%(backup_host_ip)s'
                        % {"dir": constant.Cascaded.REMOTE_SCRIPTS_DIR,
                           "config_backup_script":
                               constant.Cascaded.CONFIG_CINDER_BACKUP_SCRIPT,
                           "cascaded_domain":
                               CloudManager._domain_to_region(cascaded_domain),
                           "backup_cascaded_domain":
                               CloudManager._domain_to_region(cascaded_domain),
                           "host_ip": ceph_vms["ceph_node1_vm_ip"],
                           "backup_host_ip": ceph_vms["ceph_node1_vm_ip"]})
                break
            except SSHCommandFailure as e3:
                logger.error("config cinder backup error, error: %s"
                             % e3.message)
                time.sleep(1)

        return True

    @staticmethod
    def _domain_to_region(domain):
        domain_list = domain.split(".")
        region = domain_list[0] + "." + domain_list[1]
        return region

    @staticmethod
    def _enable_tunnel_network_cross(cloud, access_key_id, secret_key):
        vpn_info = cloud.tunnel_vpn
        # cascaded_info = cloud.cascaded_openstack
        vpn = VPN(public_ip=vpn_info["public_ip"],
                  user=VpnConstant.AWS_VPN_ROOT,
                  pass_word=VpnConstant.AWS_VPN_ROOT_PWD)

        for other_cloud_id in AwsCloudDataHandler().list_aws_clouds():
            if other_cloud_id == cloud.cloud_id:
                continue

            other_cloud = AwsCloudDataHandler().get_aws_cloud(other_cloud_id)
            if not other_cloud.access:
                continue

            conn_name = "%s-tunnel-%s" % (cloud.cloud_id, other_cloud_id)
            other_vpn_info = other_cloud.tunnel_vpn
            # other_cascaded_info = other_cloud.cascaded_openstack
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

            # add cloud-sg
            logger.info("add aws sg...")
            cascaded_installer.aws_cascaded_add_security(
                region=cloud.region,
                az=cloud.az,
                access_key_id=access_key_id,
                secret_key=secret_key,
                cidr="%s/32" % other_vpn_info["public_ip"])

            cascaded_installer.aws_cascaded_add_security(
                region=other_cloud.region,
                az=other_cloud.az,
                access_key_id=access_key_id,
                secret_key=secret_key,
                cidr="%s/32" % vpn_info["public_ip"])
        return True

    @staticmethod
    def _disable_network_cross(cloud, access_key_id, secret_key):
        # only disable other_cloud vpn
        for other_cloud_id in AwsCloudDataHandler().list_aws_clouds():
            if other_cloud_id == cloud.cloud_id:
                continue

            other_cloud = AwsCloudDataHandler().get_aws_cloud(other_cloud_id)
            if other_cloud.access == "false":
                continue

            # delete api cross
            api_conn_name = "%s-api-%s" \
                            % (cloud.cloud_id, other_cloud.cloud_id)
            api_conn_name_alter = "%s-api-%s" \
                                  % (other_cloud.cloud_id, cloud.cloud_id)
            other_api_vpn_info = other_cloud.api_vpn
            other_api_vpn = VPN(public_ip=other_api_vpn_info["public_ip"],
                                user=VpnConstant.AWS_VPN_ROOT,
                                pass_word=VpnConstant.AWS_VPN_ROOT_PWD)

            logger.info("remove conn on api vpn...")

            other_api_vpn.remove_tunnel(api_conn_name)

            other_api_vpn.remove_tunnel(api_conn_name_alter)

            other_api_vpn.restart_ipsec_service()

            # delete tunnel cross
            tunnel_conn_name = "%s-tunnel-%s" \
                               % (cloud.cloud_id, other_cloud.cloud_id)
            tunnel_conn_name_alter = "%s-tunnel-%s" \
                                     % (other_cloud.cloud_id, cloud.cloud_id)
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
            cascaded_installer.aws_cascaded_remove_security(
                region=cloud.region,
                az=cloud.az,
                access_key_id=access_key_id,
                secret_key=secret_key,
                cidr="%s/32" % cloud.api_vpn["public_ip"])

            cascaded_installer.aws_cascaded_remove_security(
                region=other_cloud.region,
                az=other_cloud.az,
                access_key_id=access_key_id,
                secret_key=secret_key,
                cidr="%s/32" % cloud.tunnel_vpn["public_ip"])

        return True

    @staticmethod
    def list_aws_cloud():
        return AwsCloudDataHandler().list_aws_clouds()

    @staticmethod
    def get_aws_cloud(cloud_id):
        return AwsCloudDataHandler().get_aws_cloud(cloud_id)

    def delete_aws_cloud(self, region_name, az_alias):
        try:
            env_info = read_environment_info()
        except ReadEnvironmentInfoFailure:
            logger.error("read environment info error. check the config file.")
            return False

        cloud_id = self._distribute_cloud_domain(
            region_name=region_name,
            az_alias=az_alias,
            az_tag="--aws")

        aws_cloud_info = AwsCloudDataHandler().get_aws_cloud(cloud_id=cloud_id)

        if aws_cloud_info is None:
            logger.error("no such cloud, cloud_id=%s" % cloud_id)
            return True

        if aws_cloud_info.driver_type == "agentless":
            logger.info("remove hyper node...")
            HyperNodeManager(
                access_key_id=aws_cloud_info.access_key_id,
                secret_key_id=aws_cloud_info.secret_key,
                region=aws_cloud_info.region,
                vpc_id=aws_cloud_info.vpc_id).start_remove_all()

        logger.info("remove aws cascaded...")
        cascaded_installer.aws_cascaded_uninstall(
            region=aws_cloud_info.region,
            az=aws_cloud_info.az,
            access_key_id=aws_cloud_info.access_key_id,
            secret_key=aws_cloud_info.secret_key)

        # config cascading
        try:
            execute_cmd_without_stdout(
                host=env_info["cascading_ip"],
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s %(cascaded_domain)s'
                    % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                       "script":
                           constant.RemoveConstant.REMOVE_AGGREGATE_SCRIPT,
                       "cascaded_domain": aws_cloud_info.cascaded_openstack[
                           "cascaded_domain"]})
        except Exception as e:
            logger.error("remove aggregate error, error: %s" % e.message)

        try:
            execute_cmd_without_stdout(
                host=env_info["cascading_ip"],
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s %(cascaded_domain)s'
                    % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                       "script":
                           constant.RemoveConstant.REMOVE_CINDER_SERVICE_SCRIPT,
                       "cascaded_domain": aws_cloud_info.cascaded_openstack[
                           "cascaded_domain"]})
        except Exception as e:
            logger.error("remove cinder service error, error: %s" % e.message)

        try:
            execute_cmd_without_stdout(
                host=env_info["cascading_ip"],
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s %(cascaded_domain)s'
                    % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                       "script":
                           constant.RemoveConstant.REMOVE_NEUTRON_AGENT_SCRIPT,
                       "cascaded_domain": aws_cloud_info.cascaded_openstack[
                           "cascaded_domain"]})

            execute_cmd_without_stdout(
                host=env_info["cascading_ip"],
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s %(proxy_host)s'
                    % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                       "script":
                           constant.RemoveConstant.REMOVE_NEUTRON_AGENT_SCRIPT,
                       "proxy_host": aws_cloud_info.proxy_info["id"]})

        except Exception as e:
            logger.error("remove neutron agent error, error: %s" % e.message)

        try:
            execute_cmd_without_stdout(
                host=env_info["cascading_ip"],
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s %(cascaded_domain)s'
                    % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                       "script": constant.RemoveConstant.REMOVE_KEYSTONE_SCRIPT,
                       "cascaded_domain": aws_cloud_info.cascaded_openstack[
                           "cascaded_domain"]})
        except SSHCommandFailure:
            logger.error("remove keystone endpoint error.")

        try:
            # ProxyManager(env_info["cascading_ip"]).release_proxy(
            #     aws_cloud_info.proxy_info["id"])
            execute_cmd_without_stdout(
                host=env_info["cascading_ip"],
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s %(proxy_host_name)s'
                    % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                       "script": constant.RemoveConstant.REMOVE_PROXY_SCRIPT,
                       "proxy_host_name": aws_cloud_info.proxy_info["id"]})
        except SSHCommandFailure:
            logger.error("remove proxy error.")

        address = "/%(cascaded_domain)s/%(cascaded_ip)s" \
                  % {"cascaded_domain":
                         aws_cloud_info.cascaded_openstack["cascaded_domain"],
                     "cascaded_ip":
                         aws_cloud_info.cascaded_openstack["api_ip"]}

        try:
            execute_cmd_without_stdout(
                host=env_info["cascading_ip"],
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s remove %(address)s'
                    % {"dir": constant.Cascading.REMOTE_SCRIPTS_DIR,
                       "script":
                           constant.PublicConstant.MODIFY_DNS_SERVER_ADDRESS,
                       "address": address})
        except SSHCommandFailure:
            logger.error("remove dns address error.")

        # config local_vpn
        try:
            local_vpn = VPN(env_info["vpn_ip"],
                            constant.VpnConstant.VPN_ROOT,
                            constant.VpnConstant.VPN_ROOT_PWD)
            local_vpn.remove_tunnel(aws_cloud_info.api_vpn["conn_name"])
            local_vpn.remove_tunnel(aws_cloud_info.tunnel_vpn["conn_name"])
        except SSHCommandFailure:
            logger.error("remove conn error.")

        # release subnet
        subnet_pair = {
            'api_subnet': aws_cloud_info.api_vpn["private_subnet"],
            'tunnel_subnet': aws_cloud_info.tunnel_vpn["private_subnet"]}
        SubnetManager().release_subnet_pair(subnet_pair)

        try:
            self._disable_network_cross(
                aws_cloud_info,
                access_key_id=aws_cloud_info.access_key_id,
                secret_key=aws_cloud_info.secret_key)
        except Exception:
            logger.error("disable network cross error.")

        AwsCloudDataHandler().delete_aws_cloud(cloud_id)

        logger.info("delete cloud success. cloud_id = %s" % cloud_id)

        return True
