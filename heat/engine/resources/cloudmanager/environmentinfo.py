# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

import os
import json

import log as logger

from exception import *

# CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
# data_file = os.path.join(CURRENT_PATH, "data", "environment_info.json")


def read_environment_info():
    env_data_file = os.path.join("/home/openstack/cloud_manager", "data", 'environment_info.json')
    if not os.path.exists(env_data_file):
        logger.error("read %s : No such file." % env_data_file)
        raise ReadEnvironmentInfoFailure(reason="read %s : No such file." % env_data_file)

    with open(env_data_file, 'r+') as fd:
        tmp = fd.read()
        return json.loads(tmp)


def write_environment_info():
    env_data_file = os.path.join("/home/openstack/cloud_manager", "data", 'environment_info.json')
    environment_info = {"cascading_ip": "",
                        "cascading_passwd": "",
                        "cascading_domain": "",
                        "additional_dns": {},
                        "vpn_ip": "",
                        "api_public_gw": "", "api_vpn_ip": "", "api_subnet": "",
                        "tunnel_public_gw": "", "tunnel_vpn_ip": '', "tunnel_subnet": ""}

    with open(env_data_file, 'w+') as fd:
        fd.write(json.dumps(environment_info, indent=4))
        return True


if __name__ == '__main__':
    logger.init('environment_info', output=True)
    write_environment_info()
    info = read_environment_info()
    logger.info(info)
