# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

from cloud import Cloud


class AwsCloud(Cloud):

    def __init__(self, cloud_id, region, az, access_key_id, secret_key,
                 cascaded_openstack, api_vpn, tunnel_vpn, vpc_id,
                 proxy_info=None, driver_type="agentleass",
                 access=True, ceph_vm=None):
        """Initialize AwsCloud.
        """
        Cloud.__init__(self, cloud_id, cascaded_openstack,
                       api_vpn, tunnel_vpn, proxy_info, access, ceph_vm)
        self.region = region
        self.az = az
        self.access_key_id = access_key_id
        self.secret_key = secret_key
        self.vpc_id = vpc_id
        self.driver_type = driver_type

