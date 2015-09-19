import threading
import os
import json

class cascaded_mutex(object): 
    g_mutex=threading.Lock()
    def get(self):
        return g_mutex
    def acquire(self):
        self.g_mutex.acquire()
    def release(self):
        self.g_mutex.release()


data_file="/home/openstack/cascadeds.json"

class data_handler(object):
    def __init__(self):
        self._lock=cascaded_mutex()
        self.file=data_file

    def lock(self):
        self._lock.acquire()
    
    def unlock(self):
        self._lock.release()

    def data_init(self):
        init_data={"sg_id":None, "v2v_id":None, "network":{"vpc_id":None, "debug_subnetid":None, "base_subnetid":None, "api_subnetid":None, "tunnel_subnetid":None, "gateway_id":None}, "cascaded":{"cascaded_vm_id":None, "cascaded_eip_public_ip":None, "cascaded_eip_allocation_id":None}, "vpn_api":{"vpn_api_vm_id":None, "vpn_api_eip_public_ip":None, "vpn_api_eip_allocation_id":None, "vpn_api_interface_id":None}, "vpn_tunnel":{"vpn_tunnel_vm_id":None, "vpn_tunnel_eip_public_ip":None, "vpn_tunnel_eip_allocation_id":None, "vpn_tunnel_interface_id":None}}
        return init_data

    def get_all(self):
        if not os.path.exists(self.file):
            with open(self.file, 'w') as fd:
                pass

            cascaded_info={}
            with open(self.file, 'w+') as fd:
                fd.write(json.dumps(cascaded_info))
            return cascaded_info
        try:
            with open(self.file, 'r+') as fd:
                tmp=fd.read()
            cascaded_info=json.loads(tmp)
        except:
            cascaded_info={}
        return cascaded_info

    def get_network(self, key):
        cascaded_info=self.get_all()
        if not cascaded_info.has_key(key):
            return None
        return cascaded_info[key]["network"]

    def write_network(self, key, vpc_id, debug_subnetid, base_subnetid, api_subnetid, tunnel_subnetid, gateway_id):
        cascaded_info=self.get_all()
        if not cascaded_info.has_key(key):
            cascaded_info[key]=self.data_init()
        cascaded_info[key]["network"]={"vpc_id":vpc_id, "debug_subnetid":debug_subnetid, "base_subnetid":base_subnetid, "api_subnetid":api_subnetid, "tunnel_subnetid":tunnel_subnetid, "gateway_id":gateway_id}
        
        with open(self.file, 'w+') as fd:
            fd.write(json.dumps(cascaded_info))

    def get_cascaded(self, key):
        cascaded_info=self.get_all()
        if not cascaded_info.has_key(key):
            return None
        return cascaded_info[key]["cascaded"]

    def write_cascaded(self, key, cascaded_vm_id, cascaded_eip_public_ip, cascaded_eip_allocation_id):
        cascaded_info=self.get_all()
        if not cascaded_info.has_key(key):
            cascaded_info[key]=self.data_init()
        cascaded_info[key]["cascaded"]={"cascaded_vm_id":cascaded_vm_id, "cascaded_eip_public_ip":cascaded_eip_public_ip, "cascaded_eip_allocation_id":cascaded_eip_allocation_id}
        
        with open(self.file, 'w+') as fd:
            fd.write(json.dumps(cascaded_info))

    def get_vpn_api(self, key):
        cascaded_info=self.get_all()
        if not cascaded_info.has_key(key):
            return None
        return cascaded_info[key]["vpn_api"]

    def write_vpn_api(self, key, vpn_api_vm_id, vpn_api_eip_public_ip, vpn_api_eip_allocation_id, vpn_api_interface_id):
        cascaded_info=self.get_all()
        if not cascaded_info.has_key(key):
            cascaded_info[key]=self.data_init()
        cascaded_info[key]["vpn_api"]={"vpn_api_vm_id":vpn_api_vm_id, "vpn_api_eip_public_ip":vpn_api_eip_public_ip, "vpn_api_eip_allocation_id":vpn_api_eip_allocation_id, "interface_id":vpn_api_interface_id}

        with open(self.file, 'w+') as fd:
            fd.write(json.dumps(cascaded_info))

    def get_vpn_tunnel(self, key):
        cascaded_info=self.get_all()
        if not cascaded_info.has_key(key):
            return None
        return cascaded_info[key]["vpn_tunnel"]

    def write_vpn_tunnel(self, key, vpn_tunnel_vm_id, vpn_tunnel_eip_public_ip, vpn_tunnel_eip_allocation_id, vpn_tunnel_interface_id):
        cascaded_info=self.get_all()
        if not cascaded_info.has_key(key):
            cascaded_info[key]=self.data_init()
        cascaded_info[key]["vpn_tunnel"]={"vpn_tunnel_vm_id":vpn_tunnel_vm_id, "vpn_tunnel_eip_public_ip":vpn_tunnel_eip_public_ip, "vpn_tunnel_eip_allocation_id":vpn_tunnel_eip_allocation_id, "interface_id":vpn_tunnel_interface_id}

        with open(self.file, 'w+') as fd:
            fd.write(json.dumps(cascaded_info))

    def get_sg_id(self, key):
        cascaded_info=self.get_all()
        if not cascaded_info.has_key(key):
            return None
        return cascaded_info[key]["sg_id"]

    def write_sg_id(self, key, sg_id):
        cascaded_info=self.get_all()
        if not cascaded_info.has_key(key):
            cascaded_info[key]=self.data_init()
        cascaded_info[key]["sg_id"]=sg_id

        with open(self.file, 'w+') as fd:
            fd.write(json.dumps(cascaded_info))

    def remove_all(self, key):
        cascaded_info=self.get_all()
        if not cascaded_info.has_key(key):
            return
        else:
            cascaded_info.pop(key)
        
        with open(self.file, 'w+') as fd:
            fd.write(json.dumps(cascaded_info))

    def get_v2v_id(self, key):
        cascaded_info=self.get_all()
        if not cascaded_info.has_key(key):
            return None
        if not cascaded_info[key].has_key("v2v_id"):
            return None
        return cascaded_info[key]["v2v_id"]

    def write_v2v_id(self, key, v2v_id):
        cascaded_info=self.get_all()
        if not cascaded_info.has_key(key):
            cascaded_info[key]=self.data_init()
        cascaded_info[key]["v2v_id"]=v2v_id

        with open(self.file, 'w+') as fd:
            fd.write(json.dumps(cascaded_info))
