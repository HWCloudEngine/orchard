# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

import log as logger
import sshclient
from commonutils import *
from constant import *


class VPN(object):

    def __init__(self, public_ip, user, pass_word):
        """Initialize VPN.
        :param public_ip: VPN public ip
        :param user: VPN ssh user
        :param pass_word: VPN ssh password
        """
        self.public_ip = public_ip
        self.user = user
        self.pass_word = pass_word
        # self.ssh = sshclient.SSH(host=self.public_ip, user=self.user, password=self.pass_word)
        # self.__copy_scripts__()

    def copy_scripts(self):
        logger.info("copy vpn config scripts to vpn host, vpn = % s" % self.public_ip)
        local_dir = VpnConstant.SCRIPTS_DIR
        remote_dir = VpnConstant.REMOTE_SCRIPTS_DIR

        execute_cmd_without_stdout(host=self.public_ip, user=self.user, password=self.pass_word,
                                   cmd='mkdir -p %(dir)s' % {"dir": VpnConstant.REMOTE_SCRIPTS_DIR})

        scp_file_to_host(host=self.public_ip, user=self.user, password=self.pass_word,
                         file_name=VpnConstant.ADD_TUNNEL_SCRIPT,
                         local_dir=VpnConstant.SCRIPTS_DIR,
                         remote_dir=VpnConstant.REMOTE_SCRIPTS_DIR)

        # scp_file_to_host(self.ssh, VpnConstant.LIST_TUNNEL_SCRIPT,
        #                  VpnConstant.SCRIPTS_DIR, VpnConstant.REMOTE_SCRIPTS_DIR)

        # scp_file_to_host(self.ssh, VpnConstant.REMOVE_TUNNEL_SCRIPT,
        #                  VpnConstant.SCRIPTS_DIR, VpnConstant.REMOTE_SCRIPTS_DIR)
        return True

    def update(self, public_ip, user, pass_word):
        """update VPN.
        :param public_ip: VPN public ip
        :param user: VPN ssh user
        :param pass_word: VPN ssh password
        """
        self.public_ip = public_ip
        self.user = user
        self.pass_word = pass_word
        # self.ssh = sshclient.SSH(host=self.public_ip, user=self.user, password=self.pass_word)

    def add_tunnel(self, tunnel_name, left, left_subnet, right, right_subnet):
        logger.info("add a new tunnel, vpn = % s, tunnel = % s" % (self.public_ip, tunnel_name))

        execute_cmd_without_stdout(host=self.public_ip, user=self.user, password=self.pass_word,
                                   cmd='cd %(dir)s; sh %(script)s '
                                       '%(tunnel_name)s %(left)s %(left_subnet)s %(right)s %(right_subnet)s'
                                   % {"dir": VpnConstant.REMOTE_SCRIPTS_DIR,
                                      "script": VpnConstant.ADD_TUNNEL_SCRIPT,
                                      "tunnel_name": tunnel_name,
                                      "left": left, "left_subnet": left_subnet,
                                      "right": right, "right_subnet": right_subnet})

        return True

    def remove_tunnel(self, tunnel_name):
        logger.info("remove tunnel, vpn = % s, tunnel = % s" % (self.public_ip, tunnel_name))

        execute_cmd_without_stdout(host=self.public_ip, user=self.user, password=self.pass_word,
                                   cmd='cd %(dir)s; sh %(script)s %(tunnel_name)s'
                                   % {"dir": VpnConstant.REMOTE_SCRIPTS_DIR,
                                      "script": VpnConstant.REMOVE_TUNNEL_SCRIPT,
                                      "tunnel_name": tunnel_name})
        return True

    def list_tunnel(self):
        logger.info("list tunnel, vpn = % s" % self.public_ip)
        tunnel_list = execute_cmd_with_stdout(host=self.public_ip, user=self.user, password=self.pass_word,
                                              cmd='cd %(dir)s; sh %(script)s'
                                              % {"dir": VpnConstant.REMOTE_SCRIPTS_DIR,
                                                 "script": VpnConstant.LIST_TUNNEL_SCRIPT})
        return tunnel_list.strip("\n").split(',')

    def restart_ipsec_service(self):
        logger.info("restart ipsec service, vpn = % s" % self.public_ip)
        execute_cmd_without_stdout(host=self.public_ip, user=self.user, password=self.pass_word,
                                   cmd="service ipsec restart")
        return True

    def up_tunnel(self, *tunnel_name):
        logger.info("up tunnel, vpn = % s" % self.public_ip)
        cmd = ""
        for name in tunnel_name:
            cmd += "ipsec auto --up %s;" % name
        execute_cmd_without_stdout(host=self.public_ip, user=self.user, password=self.pass_word, cmd=cmd)
        return True

    def check_vpn_tunnel(self, check_ip):
        """ check tunnel on this vpn.
        :return : {"exitCode":exitCode, "error_message":error_message}
        """
        # TODO
        pass