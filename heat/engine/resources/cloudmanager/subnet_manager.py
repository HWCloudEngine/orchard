# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

import threading
import os
import json
import log as logger

# __CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
# subnet_data_file = os.path.join(__CURRENT_PATH, "data", "subnet.json")
subnet_data_file = os.path.join("/home/openstack/cloud_manager", "data", "subnet.json")


class SysMutex(object):
    g_mutex = threading.Lock()

    def get(self):
        return self.g_mutex

    def acquire(self):
        self.g_mutex.acquire()

    def release(self):
        self.g_mutex.release()


class SubnetManager(object):
    def __init__(self):
        self._lock = SysMutex()
        self.file = subnet_data_file

    def __lock(self):
        self._lock.acquire()

    def __unlock(self):
        self._lock.release()

    def distribute_subnet_pair(self):
        """
        :return:{'api_subnet': '172.29.0.0/24', 'tunnel_subnet': '172.29.1.0/24'}
        """
        subnets_info = self.__get_subnet_info__()

        if subnets_info["free"] > 0:
            subnet_id = subnets_info["free_subnet"].pop()
        else:
            subnet_id = subnets_info["total"]
            while subnet_id in subnets_info["free_subnet"] or subnet_id in  subnets_info["active_subnet"]:
                subnet_id += 1

        subnets_info["active_subnet"].append(subnet_id)
        subnets_info["free"] = len(subnets_info["free_subnet"])
        subnets_info["total"] = len(subnets_info["free_subnet"]) + len(subnets_info["active_subnet"])

        with open(self.file, 'w+') as fd:
            fd.write(json.dumps(subnets_info, indent=4))

        api_subnet = '172.29.%s.0/24' % subnet_id
        tunnel_subnet = '172.29.%s.0/24' % (subnet_id+128)

        return {'api_subnet': api_subnet, 'tunnel_subnet': tunnel_subnet}

    def release_subnet_pair(self, subnet_pair):
        api_subnet = subnet_pair['api_subnet']
        tunnel_subnet = subnet_pair['tunnel_subnet']

        api_subnet_id = api_subnet.split(".")[2]
        tunnel_subnet_id = tunnel_subnet.split(".")[2]

        subnet_id = int(api_subnet_id)

        subnet_info = self.__get_subnet_info__()

        if subnet_id in subnet_info["active_subnet"]:
            subnet_info["active_subnet"].remove(subnet_id)
            subnet_info["free_subnet"].append(subnet_id)
            subnet_info["free"] = len(subnet_info["free_subnet"])

        with open(self.file, 'w+') as fd:
            fd.write(json.dumps(subnet_info, indent=4))
        return True

    def __get_subnet_info__(self):
        if not os.path.exists(self.file):
            subnet_info = {"free_subnet": [], "active_subnet": [], "total": 0, "free": 0}
        else:
            with open(self.file, 'r+') as fd:
                tmp = fd.read()
                subnet_info = json.loads(tmp)
        return subnet_info
