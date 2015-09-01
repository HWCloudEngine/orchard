# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

import threading
import json
import random
import log as logger
import constant
from commonutils import *
import install.proxy_installer as proxy_installer


class SysMutex(object):
    g_mutex = threading.Lock()

    def get(self):
        return self.g_mutex

    def acquire(self):
        self.g_mutex.acquire()

    def release(self):
        self.g_mutex.release()

# CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
# data_file = os.path.join(CURRENT_PATH, "data", "proxys.json")
proxy_data_file = os.path.join("/home/openstack/cloud_manager", "data", "proxys.json")


class ProxyManager(object):
    def __init__(self, cascading_ip):
        self._lock = SysMutex()
        self.file = proxy_data_file
        self.cascading_ip = cascading_ip

    def lock(self):
        self._lock.acquire()
    
    def unlock(self):
        self._lock.release()

    def next_proxy_name(self):
        proxy_info = self.__get_proxy_info__()

        if proxy_info["free"] > 0:
            for proxy_host_neme in proxy_info["free_proxy"].keys():
                right_proxy = self.__active_proxy__(proxy_info, proxy_host_neme)
                break

            if proxy_info["free"] <= 1:
                # add a proxy
                proxy_installer.proxy_install()
        else:
            right_proxy = None
            # add a proxy
            proxy_installer.proxy_install()

        with open(proxy_data_file, 'w+') as fd:
            fd.write(json.dumps(proxy_info, indent=4))

        return right_proxy

    def release_proxy(self, proxy_host_name):
        proxy_info = self.__get_proxy_info__()
        release_proxy=self.__add_free_proxy__(proxy_info, proxy_host_name)
        with open(proxy_data_file, 'w+') as fd:
            fd.write(json.dumps(proxy_info, indent=4))
        return release_proxy

    def __create_proxy_num__(self, total):
        if total > 3:
            sed = 2 * total
        else:
            sed = 6
        return str(random.randint(2, sed)).zfill(3)

    def __get_proxy_info__(self):
        if not os.path.exists(proxy_data_file):
            proxy_info = {"free_proxy": {}, "active_proxy": {}, "total": 0, "free": 0}
        else:
            with open(proxy_data_file, 'r+') as fd:
                tmp = fd.read()
                proxy_info = json.loads(tmp)

        system_free_proxy_host_name_list = self.__check_free_proxy__()
        for proxy_host_name in proxy_info["free_proxy"].keys():
            if proxy_host_name in system_free_proxy_host_name_list:
                pass
            else:
                self.__active_proxy__(proxy_info, proxy_host_name)

        for proxy_host_neme in system_free_proxy_host_name_list:
            if proxy_host_neme not in proxy_info["free_proxy"].keys():
                self.__add_free_proxy__(proxy_info, proxy_host_neme)

        return proxy_info

    def __active_proxy__(self, proxy_info, proxy_host_neme):
        proxy_num = proxy_info["free_proxy"].pop(proxy_host_neme)
        proxy_info["active_proxy"][proxy_host_neme]=proxy_num
        free = proxy_info["free"]
        proxy_info["free"] = free - 1

        return {"host_name": proxy_host_neme, "proxy_num": proxy_num}

    def __add_free_proxy__(self, proxy_info, proxy_host_name):
        if proxy_host_name in proxy_info["active_proxy"].keys():
            proxy_num = proxy_info["active_proxy"].pop(proxy_host_name)
            total = proxy_info["total"]
            proxy_info["total"] = total - 1
        else:
            proxy_num = "proxy"+self.__create_proxy_num__(proxy_info["total"])
            while proxy_num in proxy_info["active_proxy"].values() or proxy_num in proxy_info["free_proxy"].values():
                proxy_num = "proxy"+self.__create_proxy_num__(proxy_info["total"])

        proxy_info["free_proxy"][proxy_host_name] = proxy_num
        free = proxy_info["free"]
        proxy_info["free"] = free + 1
        total = proxy_info["total"]
        proxy_info["total"] = total + 1
        return {"host_name": proxy_host_name, "proxy_num": proxy_num}

    def __check_free_proxy__(self):
        temp = execute_cmd_with_stdout(host=self.cascading_ip,
                                       user=constant.Cascading.ROOT, password=constant.Cascading.ROOT_PWD,
                                       cmd='cd %(dir)s; sh %(script)s'
                                           % {"dir": constant.Cascading.REMOTE_SCRIPTS_DIR,
                                              "script":constant.Cascading.CHECK_PROXY_SCRIPT})
        free_proxy = temp.strip("\n").split(",")
        return free_proxy

