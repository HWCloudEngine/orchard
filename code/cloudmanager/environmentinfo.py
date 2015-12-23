# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

import os
import json

from exception import *

env_data_file = os.path.join("/home/hybrid_cloud/conf",
                             'environment.conf')


def read_environment_info():
    if not os.path.exists(env_data_file):
        logger.error("read %s : No such file." % env_data_file)
        raise ReadEnvironmentInfoFailure(reason="read %s : No such file."
                                                % env_data_file)
    with open(env_data_file, 'r+') as fd:
        tmp = fd.read()
        return json.loads(tmp)


def write_environment_info():
    environment_info = {"env": "/root/adminrc",
                        "cascading_api_ip": "162.3.121.2",
                        "cascading_domain": "cloud.hybrid.huawei.com",
                        "local_vpn_ip": "162.3.121.254",
                        "local_vpn_public_gw": "205.177.226.131",
                        "local_api_subnet": "162.3.0.0/16",
                        "local_vpn_api_ip": "162.3.121.254",
                        "local_tunnel_subnet": "172.28.48.0/20",
                        "local_vpn_tunnel_ip": "172.28.48.254",
                        "existed_cascaded": []}

    with open(env_data_file, 'w+') as fd:
        fd.write(json.dumps(environment_info, indent=4))
        return True


if __name__ == '__main__':
    write_environment_info()
    info = read_environment_info()
