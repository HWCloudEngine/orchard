# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

import time
import log as logger

import commonutils
import constant
import exception


class CascadingConfiger(object):
    def __init__(self, api_ip, user, password, cascaded_domain, cascaded_ip, v2v_gw):
        self.api_ip = api_ip
        self.user = user
        self.password = password
        self.cascaded_domain = cascaded_domain
        self.cascaded_ip = cascaded_ip
        self.v2v_gw = v2v_gw

    def do_config(self):
        start_time = time.time()
        logger.info("start config cascading, cascading: %s" % self.api_ip)

        # modify dns server address
        address = "/%(cascaded_domain)s/%(cascaded_ip)s" \
                  % {"cascaded_domain": self.cascaded_domain,
                     "cascaded_ip": self.cascaded_ip}

        for i in range(3):
            try:
                commonutils.execute_cmd_without_stdout(
                    host=self.api_ip,
                    user=self.user,
                    password=self.password,
                    cmd='cd %(dir)s; sh %(script)s add %(address)s'
                        % {"dir": constant.Cascading.REMOTE_SCRIPTS_DIR,
                           "script": constant.PublicConstant.MODIFY_DNS_SERVER_ADDRESS,
                           "address": address})
                break
            except exception.SSHCommandFailure as e:
                logger.error("modify cascading dns address error, cascaded: %s, error: %s"
                             % (self.cascaded_domain, e.format_message()))
                time.sleep(1)

        logger.info("config cascading dns address success, cascading: %s" % self.api_ip)

        # config keystone
        for i in range(3):
            try:
                commonutils.execute_cmd_without_stdout(
                    host=self.api_ip,
                    user=self.user,
                    password=self.password,
                    cmd='cd %(dir)s; sh %(script)s %(cascaded_domain)s %(v2v_gw)s'
                        % {"dir": constant.Cascading.REMOTE_SCRIPTS_DIR,
                           "script": constant.Cascading.KEYSTONE_ENDPOINT_SCRIPT,
                           "cascaded_domain": self.cascaded_domain,
                           "v2v_gw": self.v2v_gw})
                break
            except exception.SSHCommandFailure as e:
                logger.error("create keystone endpoint error, cascaded: %s, error: %s"
                             % (self.cascaded_domain, e.format_message()))
                time.sleep(1)

        logger.info("config cascading keystone success, cascading: %s" % self.api_ip)

        for i in range(3):
            try:
                commonutils.execute_cmd_without_stdout(
                    host=self.api_ip,
                    user=self.user,
                    password=self.password,
                    cmd='cd %(dir)s; sh %(script)s %(cascaded_domain)s'
                        % {"dir": constant.Cascading.REMOTE_SCRIPTS_DIR,
                           "script": constant.Cascading.ENABLE_OPENSTACK_SERVICE,
                           "cascaded_domain": self.cascaded_domain})
                break
            except exception.SSHCommandFailure as e:
                logger.error("enable openstack service error, cascaded: %s, error: %s"
                             % (self.cascaded_domain, e.format_message()))
                time.sleep(1)

        logger.info("enable openstack service success, cascading: %s" % self.api_ip)
        cost_time = time.time() - start_time
        logger.info("config cascading success, cascading: %s, cost time: %d" % (self.api_ip, cost_time))
