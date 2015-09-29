# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

import time
import log as logger

import commonutils
import constant
import exception


class CascadedConfiger(object):
    def __init__(self, api_ip, tunnel_ip, domain, user, password,
                 cascading_domain, cascading_ip):
        self.api_ip = api_ip
        self.tunnel_ip = tunnel_ip
        self.domain = domain
        self.user = user
        self.password = password
        self.cascading_domain = cascading_domain
        self.cascading_ip = cascading_ip

    def do_config(self):
        start_time = time.time()
        logger.info("start config cascaded, cascaded: %s" % self.domain)
        # wait cascaded tunnel can visit
        commonutils.check_host_status(host=self.tunnel_ip,
                                      user=self.user,
                                      password=self.password,
                                      retry_time=100, interval=1)

        # config cascaded host
        self._config_az_cascaded()

        time.sleep(20)

        self._config_az_cascaded()

        cost_time = time.time() - start_time
        logger.info("first config success,  cascaded: %s, cost time: %d" % (self.domain, cost_time))

        # check config result
        for i in range(3):
            try:
                # check 120s
                commonutils.check_host_status(host=self.api_ip,
                                              user=constant.Cascaded.ROOT,
                                              password=constant.Cascaded.ROOT_PWD,
                                              retry_time=15,
                                              interval=1)
                logger.info("cascaded api is ready..")
                break
            except exception.CheckHostStatusFailure as e:
                if i == 2:
                    logger.error("check cascaded api failed ...")
                    break
                logger.error("check cascaded api error, "
                             "retry config cascaded ...")
                self._config_az_cascaded()

        cost_time = time.time() - start_time
        logger.info("config cascaded success, cascaded: %s, cost_time: %d" % (self.domain, cost_time))

    def _config_az_cascaded(self):
        logger.info("start config cascaded host, host: %s" % self.tunnel_ip)
        cascaded_ip = self.tunnel_ip
        gateway = _get_gateway(self.api_ip)
        for i in range(30):
            try:
                commonutils.execute_cmd_without_stdout(
                    host=self.tunnel_ip,
                    user=constant.Cascaded.ROOT,
                    password=constant.Cascaded.ROOT_PWD,
                    cmd='cd %(dir)s; python %(script)s '
                        '%(cascading_domain)s %(cascading_ip)s '
                        '%(cascaded_domain)s %(cascaded_ip)s '
                        '%(gateway)s'
                        % {"dir": constant.Cascaded.REMOTE_SCRIPTS_DIR,
                           "script": constant.Cascaded.MODIFY_CASCADED_SCRIPT_PY,
                           "cascading_domain": self.cascading_domain,
                           "cascading_ip": self.cascading_ip,
                           "cascaded_domain": self.domain,
                           "cascaded_ip": self.api_ip,
                           "gateway": gateway})
                break
            except exception.SSHCommandFailure as e:
                logger.error("modify cascaded domain error: %s"
                             % e.format_message())
                time.sleep(5)
        return True


def _get_gateway(ip, mask=None):
    arr = ip.split(".")
    gateway = "%s.%s.%s.1" % (arr[0], arr[1], arr[2])
    return gateway
