import threading
import os
import json

class sys_mutex(object): 
    g_mutex=threading.Lock()
    def get(self):
        return g_mutex
    def acquire(self):
        self.g_mutex.acquire()
    def release(self):
        self.g_mutex.release()


data_file="/home/openstack/proxys.json"

class data_handler(object):
    def __init__(self):
        self._lock=sys_mutex()
        self.file=data_file

    def lock(self):
        self._lock.acquire()
    
    def unlock(self):
        self._lock.release()

    def get_proxy_info(self):
        if not os.path.exists(self.file):
            with open(self.file, 'w') as fd:
                pass
            
            proxy_info={"total":0, "free":0, "free_mems":[], "active_mems":[]}
            with open(self.file, 'w+') as fd:
                fd.write(proxy_info)
            return proxy_info
        try:
            with open(self.file, 'r+') as fd:
                tmp=fd.read()
            proxy_info=json.loads(tmp)
        except:
            proxy_info={"total":0, "free":0, "free_mems":[], "active_mems":[]}

        return proxy_info

    def active_mem(self, mem_name):
        proxy_info=self.get_proxy_info()
        proxy_info["free_mems"].remove(mem_name)
        proxy_info["active_mems"].append(mem_name)
        proxy_info["free"]=proxy_info["free"]-1

        with open(self.file, 'w+') as fd:
            fd.write(json.dumps(proxy_info))

    def free_mem(self, mem_name):
        proxy_info=self.get_proxy_info()
        proxy_info["free_mems"].append(mem_name)
        proxy_info["active_mems"].remove(mem_name)
        proxy_info["free"]=proxy_info["free"]+1

        with open(self.file, 'w+') as fd:
            fd.write(json.dumps(proxy_info))

    def add_active_mem(self, mem_name):
        proxy_info=self.get_proxy_info()
        proxy_info["active_mems"].append(mem_name)
        proxy_info["total"]=proxy_info["total"]+1

        with open(self.file, 'w+') as fd:
            fd.write(json.dumps(proxy_info))

    def remove_active_mem(self, mem_name):
        proxy_info=self.get_proxy_info()
        proxy_info["active_mems"].remove(mem_name)
        proxy_info["total"]=proxy_info["total"]-1

        with open(self.file, 'w+') as fd:
            fd.write(json.dumps(proxy_info))
