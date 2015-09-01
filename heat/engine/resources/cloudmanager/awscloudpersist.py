# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

import threading
from awscloud import AwsCloud
from environmentinfo import *
from commonutils import *
import log as logger


def aws_cloud_2_dict(obj):
    result = {}
    result.update(obj.__dict__)
    return result


def dict_2_aws_cloud(dict):

    if "access" in dict.keys():
        access = dict["access"]
    else:
        access = "True"

    aws_cloud = AwsCloud(cloud_id=dict["cloud_id"], region=dict["region"], az=dict["az"],
                       access_key_id=dict["access_key_id"], secret_key=dict["secret_key"],
                       cascaded_openstack=dict["cascaded_openstack"],
                       api_vpn=dict["api_vpn"], tunnel_vpn=dict["tunnel_vpn"],
                       proxy_info=dict["proxy_info"], access=access)
    return aws_cloud

class SysMutex(object):
    g_mutex = threading.Lock()

    def get(self):
        return self.g_mutex

    def acquire(self):
        self.g_mutex.acquire()

    def release(self):
        self.g_mutex.release()


# CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
# data_file = os.path.join(CURRENT_PATH, "data", 'aws_cloud.json')
aws_data_file = os.path.join("/home/openstack/cloud_manager", "data", 'aws_cloud.json')


class AwsCloudDataHandler(object):

    def __init__(self):
        self._lock = SysMutex()
        self.file = aws_data_file

    def lock(self):
        self._lock.acquire()

    def unlock(self):
        self._lock.release()

    def list_aws_clouds(self):
        cloud_dicts = self.__read_aws_cloud_info__()
        return cloud_dicts.keys()

    def get_aws_cloud(self, cloud_id):
        cloud_dicts = self.__read_aws_cloud_info__()
        if cloud_id in cloud_dicts.keys():
            return dict_2_aws_cloud(cloud_dicts[cloud_id])
        raise ReadCloudInfoFailure(reason="no such cloud, cloud_id=%s" % cloud_id)

    def delete_aws_cloud(self, cloud_id):
        cloud_dicts = self.__read_aws_cloud_info__()
        cloud_dicts.pop(cloud_id)
        with open(aws_data_file, 'w+') as fd:
            fd.write(json.dumps(cloud_dicts, indent=4))

    def add_aws_cloud(self, aws_cloud):
        if not os.path.exists(aws_data_file):
            cloud_dicts = {}
        else:
            with open(aws_data_file, 'r+') as fd:
                cloud_dicts = json.loads(fd.read())

        dict_temp = aws_cloud_2_dict(aws_cloud)

        cloud_dicts[aws_cloud.cloud_id] = dict_temp

        with open(aws_data_file, 'w+') as fd:
            fd.write(json.dumps(cloud_dicts, indent=4))

    def __read_aws_cloud_info__(self):
        if not os.path.exists(aws_data_file):
            logger.error("read %s : No such file." % aws_data_file)
            raise ReadCloudInfoFailure(reason="read %s : No such file." % aws_data_file)

        with open(aws_data_file, 'r+') as fd:
            tmp = fd.read()
            cloud_dicts = json.loads(tmp)

        return cloud_dicts
