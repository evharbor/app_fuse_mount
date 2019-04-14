#!/usr/bin/python36
#from __future__ import print_function, absolute_import, division

import logging
import os

from time import time
from stat import S_IFDIR, S_IFREG
from errno import EACCES
from os.path import realpath
from threading import Lock
from fuse import FUSE, FuseOSError, Operations, LoggingMixIn, fuse_get_context

import pyharbor

class Harbor(LoggingMixIn, Operations):
    def __init__(self, args):
        print('初始化文件系统, 示例把 / 映射到挂载目录')
        self.bucket_name   = args.bucket_name
        self.test_sys_root = realpath('/')
        pyharbor.set_global_settings({    # 配置对象存储链接
        'SCHEME': 'http',   # 或'https', 默认'https'
        'DOMAIN_NAME': 'obs.casearth.cn', # 默认 'obs.casearth.cn'
        'ACCESS_KEY': args.access_key,
        'SECRET_KEY': args.secret_key,
        })
        self.harbor_client = pyharbor.get_client()

        self.rwlock = Lock()

    def __call__(self, op, path, *args):
        return super(Harbor, self).__call__(op, self.test_sys_root + path, *args)

    def access(self, path, mode):
        if not os.access(path, mode):
            raise FuseOSError(EACCES)

    chmod = os.chmod
    chown = os.chown

    def create(self, path, mode):
        return os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)

    def flush(self, path, fh):
        return os.fsync(fh)

    def fsync(self, path, datasync, fh):
        if datasync != 0:
            return os.fdatasync(fh)
        else:
            return os.fsync(fh)

    def getattr(self, path, fh=None):
        uid, gid, pid = fuse_get_context()
        if path == '/' or '//' == path:
            st = dict(st_mode=(S_IFDIR | 0o755), st_nlink=2)
        else:
            st = dict(st_mode=(S_IFREG | 0o444), st_size=8888)
        st['st_ctime'] = st['st_mtime'] = st['st_atime'] = time()
        return st

    getxattr = None

    def link(self, target, source):
        return os.link(self.test_sys_root + source, target)

    listxattr = None
    mkdir = os.mkdir
    mknod = os.mknod
    open = os.open

    def read(self, path, size, offset, fh):
        with self.rwlock:
            os.lseek(fh, offset, 0)
            return os.read(fh, size)

    def readdir(self, path, fh):
        return_list = ['.', '..']
        this_dir = self.harbor_client.bucket(self.bucket_name).dir(path)
        data, code, msg = this_dir.get_objs_and_subdirs()
        if data:
            objs = this_dir.get_objs(data)
            for obj in objs:
                return_list.append(obj['name'])
        return return_list

    readlink = os.readlink

    def release(self, path, fh):
        return os.close(fh)

    def rename(self, old, new):
        return os.rename(old, self.test_sys_root + new)

    rmdir = os.rmdir

    def statfs(self, path):
        stv = os.statvfs(path)
        return dict((key, getattr(stv, key)) for key in (
            'f_bavail', 'f_bfree', 'f_blocks', 'f_bsize', 'f_favail',
            'f_ffree', 'f_files', 'f_flag', 'f_frsize', 'f_namemax'))

    def symlink(self, target, source):
        return os.symlink(source, target)

    def truncate(self, path, length, fh=None):
        with open(path, 'r+') as f:
            f.truncate(length)

    unlink = os.unlink
    utimens = os.utime

    def write(self, path, data, offset, fh):
        with self.rwlock:
            os.lseek(fh, offset, 0)
            return os.write(fh, data)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('bucket_name')
    parser.add_argument('mount')
    parser.add_argument('access_key')
    parser.add_argument('secret_key')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)
    fuse = FUSE(
        Harbor(args), args.mount, foreground=True, allow_other=True)
