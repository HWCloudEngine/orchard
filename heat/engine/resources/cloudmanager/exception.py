# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

import log as logger


class CloudManagerException(Exception):
    """Base CloudManager Exception

    To correctly use this class, inherit from it and define
    a 'msg_fmt' property. That msg_fmt will get printf'd
    with the keyword arguments provided to the constructor.

    """
    msg_fmt = "An unknown exception occurred."
    code = 500
    headers = {}
    safe = False

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs

        if 'code' not in self.kwargs:
            try:
                self.kwargs['code'] = self.code
            except AttributeError:
                pass

        if not message:
            try:
                message = self.msg_fmt % kwargs

            except Exception:
                # kwargs doesn't match a variable in the message
                # log the issue and the kwargs
                logger.exception('Exception in string format operation')
                for name, value in kwargs.iteritems():
                    logger.error("%s: %s" % (name, value))  # noqa

                else:
                    # at least get the core message out if something happened
                    message = self.msg_fmt

        super(CloudManagerException, self).__init__(message)

    def format_message(self):
        # NOTE(mrodden): use the first argument to the python Exception object
        # which should be our full NovaException message, (see __init__)
        return self.args[0]


class ReadEnvironmentInfoFailure(CloudManagerException):
    msg_fmt = "failed to read environment info : %(reason)s"


class ReadProxyDataFailure(CloudManagerException):
    msg_fmt = "failed to read proxy data : %(reason)s"


class SSHCommandFailure(CloudManagerException):
    msg_fmt = "failed to execute ssh command : host=%(host)s, command=%(command)s, reason=%(reason)s"


class ScpFileToHostFailure(CloudManagerException):
    msg_fmt = "spc file to host failed, host=%(host)s, file_name=%(file_name)s, " \
              "local_dir=%(local_dir)s, remote_dir=%(remote_dir)s, reason =%(reason)s"


class PersistCloudInfoFailure(CloudManagerException):
    msg_fmt = "failed to Persist cloud info : %(reason)s"


class ReadCloudInfoFailure(CloudManagerException):
    msg_fmt = "failed to read cloud info : %(reason)s"


class InstallCascadedHostFailure(CloudManagerException):
    msg_fmt = "failed to install cascaded host : %(reason)s"

class InstallCascadedFailure(CloudManagerException):
    msg_fmt = "failed to install cascaded basic environment : %(reason)s"


class UninstallCascadedFailure(CloudManagerException):
    msg_fmt = "failed to uninstall cascaded basic environment : %(reason)s"


class CheckHostStatusFailure(CloudManagerException):
    msg_fmt = "failed to check host status : %(reason)s"


class ConfigCascadedHostFailure(CloudManagerException):
    msg_fmt = "failed to config cascaded host : %(reason)s"


class ConfigProxyFailure(CloudManagerException):
    msg_fmt = "failed to config proxy : %(reason)s"

