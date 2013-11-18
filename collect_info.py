#!/usr/bin/env python

import os
import platform
import shlex
import shutil
import sys
import tempfile
from subprocess import Popen, PIPE
from zipfile import ZipFile, ZIP_DEFLATED


DEVNULL = open(os.devnull, 'w')


class CollecInfo(object):

    def __init__(self):
        self.tempdir = tempfile.mkdtemp(prefix='collect_info')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            return

        zf = ZipFile('collect_info.zip', 'w', compression=ZIP_DEFLATED)
        for root, dirs, files in os.walk(self.tempdir):
            for f in files:
                zf.write(os.path.join(root, f), f)
        zf.close()
        shutil.rmtree(self.tempdir)

    def __call__(self, *args, **kwargs):
        raise NotImplementedError

    def run_cmd(self, task, cmd):
        print('Running task: {0}'.format(task))
        p = Popen(args=shlex.split(cmd), stdout=PIPE, stderr=DEVNULL)
        stdout, stderr = p.communicate()
        if p.returncode:
            print('Failed: {0}'.format(task))
        else:
            return stdout

    def store_stdout(self, task, stdout):
        out_file = '{0}/{1}'.format(self.tempdir, task)
        with open(out_file, 'w') as fh:
            fh.write(stdout.decode('utf-8'))


class LinuxCollecInfo(CollecInfo):

    TASKS = (
        ('df', 'df -ha'),
        ('dmesg', 'dmesg'),
        ('free', 'free -h'),
        ('lsmod', 'lsmod'),
        ('mpstat', 'mpstat 1 10'),
        ('netstat', 'netstat -anp'),
        ('top', 'top -Hb -n 1'),
        ('uname', 'uname -a'),

        ('cpuinfo', 'cat /proc/cpuinfo'),
        ('diskstats', 'cat /proc/diskstats'),
        ('meminfo', 'cat /proc/meminfo'),
        ('mounts', 'cat /proc/mounts'),
        ('netstat_raw', 'cat /proc/net/netstat'),
        ('vmstat', 'cat /proc/vmstat'),

        ('cmdline', 'cat /proc/{0}/cmdline'),
        ('environ', 'cat /proc/{0}/environ'),
        ('limits', 'cat /proc/{0}/limits'),
        ('pmap', 'pmap {0}'),
        ('status', 'cat /proc/{0}/status'),

        ('manifest.xml', 'cat /opt/couchbase-sync-gateway/manifest.xml'),
        ('runtime_stats', 'curl -s http://127.0.0.1:4985/_stats'),
    )

    def __init__(self):
        super(LinuxCollecInfo, self).__init__()
        self.pid = self.run_cmd('pgrep', 'pgrep sync_gateway')
        if self.pid:
            self.pid = self.pid.rstrip().decode('utf-8')

    def __call__(self):
        for task, cmd in self.TASKS:
            stdout = self.run_cmd(task, cmd.format(self.pid))
            if stdout:
                self.store_stdout(task, stdout)


def main():
    if platform.system() == 'Linux':
        with LinuxCollecInfo() as collect_info:
            collect_info()
    else:
        sys.exit('Unsupported platform')


if __name__ == '__main__':
    main()
