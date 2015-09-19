# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

import os

import sshclient

from exception import *


def check_ssh_server(host, user, password):
    ssh = sshclient.SSH(host=host, user=user, password=password)
    try:
        operate_result = ssh.execute("ls")
    except (sshclient.SSHError, sshclient.SSHTimeout) as e:
        return False

    return True


def execute_cmd_without_stdout(host, user, password, cmd):
    logger.debug("execute ssh command, host = %s, cmd = %s" % (host, cmd))
    ssh = sshclient.SSH(host=host, user=user, password=password)
    try:
        operate_result = ssh.execute(cmd)
    except (sshclient.SSHError, sshclient.SSHTimeout) as e:
        logger.error("execute ssh command failed: host = %s, cmd = %s, reason = %s" % (ssh.host, cmd, e.message))
        raise SSHCommandFailure(host=ssh.host, command=cmd, reason=e.message)
    finally:
        ssh.close()

    exit_code = operate_result[0]
    if exit_code == 0:
        return True
    else:
        logger.error(
            "execute ssh command failed: host = %s, cmd = %s, reason = %s" % (ssh.host, cmd, operate_result[2]))
        raise SSHCommandFailure(host=ssh.host, command=cmd, reason=operate_result[2])


def execute_cmd_with_stdout(host, user, password, cmd):
    logger.debug("execute ssh command, host = %s, cmd = %s" % (host, cmd))
    ssh = sshclient.SSH(host=host, user=user, password=password)
    try:
        operate_result = ssh.execute(cmd)
    except (sshclient.SSHError, sshclient.SSHTimeout) as e:
        logger.error("execute ssh command failed: host = %s, cmd = %s, reason = %s"
                     % (ssh.host, cmd, e.message))
        raise SSHCommandFailure(host=ssh.host, command=cmd, reason=e.message)
    finally:
        ssh.close()

    exit_code = operate_result[0]
    if exit_code == 0:
        return operate_result[1]
    else:
        logger.error("execute ssh command failed: host = %s, cmd = %s, reason = %s"
                     % (ssh.host, cmd, operate_result[2]))
        raise SSHCommandFailure(host=ssh.host, command=cmd, reason=operate_result[2])


def scp_file_to_host(host, user, password, file_name, local_dir, remote_dir):
    logger.debug("spc file to host, host = %s, file_name = %s, "
                 "local_dir = %s, remote_dir = %s"
                 % (host, file_name, local_dir, remote_dir))
    ssh = sshclient.SSH(host=host, user=user, password=password)
    try:
        ssh.put_file(os.path.join(local_dir, file_name), remote_dir + "/" + file_name)
    except (sshclient.SSHError, sshclient.SSHTimeout) as e:
        logger.error("spc file to host failed, host = %s, "
                     "file_name = %s, local_dir = %s, remote_dir = %s, reason = %s"
                     % (ssh.host, file_name, local_dir, remote_dir, e.message))
        raise ScpFileToHostFailure(host=ssh.host, file_name=file_name,
                                   local_dir=local_dir,
                                   remote_dir=remote_dir,
                                   reason=e.message)
    finally:
        ssh.close()

    return True


def object2dict(obj):
    # convert object to a dict
    d = {'__class__': obj.__class__.__name__, '__module__': obj.__module__}
    d.update(obj.__dict__)
    return d


def dict2object(d):
    # convert dict to object
    if '__class__' in d:
        class_name = d.pop('__class__')
        module_name = d.pop('__module__')
        module = __import__(module_name)
        class_ = getattr(module, class_name)
        args = dict((key.encode('utf-8'), value) for key, value in d.items())  # get args
        inst = class_(**args)  # create new instance
    else:
        inst = d
    return inst


def decode(cipher_text):
    return cipher_text


def encrypt(text):
    return text
