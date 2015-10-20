# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

import threading
import json
import multiprocessing

import constant
from commonutils import *
import install.proxy_installer as proxy_installer

proxy_data_file = os.path.join("/home/openstack/cloud_manager/data"
                               , "proxys.json")
proxy_manager_lock = threading.Lock()


class ProxyManager(object):
    def __init__(self, cascading_ip):
        self.cascading_ip = cascading_ip

    def next_proxy_name(self):
        proxy_manager_lock.acquire()
        try:
            proxy_info = self.__get_proxy_info__()
            if proxy_info["free"] > 0:
                for proxy_host_name in proxy_info["free_proxy"].keys():
                    right_proxy = self.__active_proxy__(proxy_info,
                                                        proxy_host_name)
                    break

                if proxy_info["free"] < 1:
                    # add a proxy, this time have a free proxy,
                    # so we need not wait the new proxy install
                    p = multiprocessing.Process(
                        target=proxy_installer.proxy_install)
                    p.start()
                    # proxy_installer.proxy_install()
            else:
                right_proxy = None
                # add a proxy, we must wait proxy install
                proxy_installer.proxy_install()

            with open(proxy_data_file, 'w+') as fd:
                fd.write(json.dumps(proxy_info, indent=4))

            return right_proxy
        except Exception as e:
            logger.error("get next proxy name error, error: %s" % e.message)
        finally:
            proxy_manager_lock.release()

    def release_proxy(self, proxy_host_name):
        proxy_manager_lock.acquire()
        try:
            proxy_info = self.__get_proxy_info__()
            release_proxy = self.__add_free_proxy__(proxy_info, proxy_host_name)
            with open(proxy_data_file, 'w+') as fd:
                fd.write(json.dumps(proxy_info, indent=4))
            return release_proxy
        except Exception as e:
            logger.error("release proxy error, proxy_host_name: %s, error: %s"
                         % (proxy_host_name, e.message))
        finally:
            proxy_manager_lock.release()

    def __get_proxy_info__(self):
        if not os.path.exists(proxy_data_file):
            proxy_info = {"free_proxy": {}, "active_proxy": {},
                          "total": 0, "free": 0}
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

    @staticmethod
    def __active_proxy__(proxy_info, proxy_host_name):
        proxy_num = proxy_info["free_proxy"].pop(proxy_host_name)
        proxy_info["active_proxy"][proxy_host_name] = proxy_num
        proxy_info["free"] = len(proxy_info["free_proxy"])

        return {"host_name": proxy_host_name, "proxy_num": proxy_num}

    @staticmethod
    def __add_free_proxy__(proxy_info, proxy_host_name):
        if proxy_host_name in proxy_info["active_proxy"].keys():
            proxy_num = proxy_info["active_proxy"].pop(proxy_host_name)
            proxy_info["total"] = \
                len(proxy_info["free_proxy"]) + len(proxy_info["active_proxy"])
        else:
            num = proxy_info["total"] + 1
            proxy_num = "proxy" + str(num).zfill(3)
            while proxy_num in proxy_info["active_proxy"].values() \
                    or proxy_num in proxy_info["free_proxy"].values():
                num += 1
                proxy_num = "proxy" + str(num).zfill(3)

        proxy_info["free_proxy"][proxy_host_name] = proxy_num
        proxy_info["free"] = len(proxy_info["free_proxy"])
        proxy_info["total"] = \
            len(proxy_info["free_proxy"]) + len(proxy_info["active_proxy"])
        return {"host_name": proxy_host_name, "proxy_num": proxy_num}

    def __check_free_proxy__(self):
        temp = execute_cmd_with_stdout(
            host=self.cascading_ip,
            user=constant.Cascading.ROOT,
            password=constant.Cascading.ROOT_PWD,
            cmd='cd %(dir)s; sh %(script)s'
                % {"dir": constant.Cascading.REMOTE_SCRIPTS_DIR,
                   "script": constant.Cascading.CHECK_PROXY_SCRIPT})
        free_proxy = temp.strip("\n").split(",")
        return free_proxy
