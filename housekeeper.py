#!/usr/bin/python
# -*- coding: UTF-8 -*-
r"""
@author: Martin Klapproth <martin.klapproth@googlemail.com>
"""
import argparse
from copy import deepcopy
from genericpath import isfile, isdir
from glob import glob
import os
from os.path import join, islink
from subprocess import Popen, PIPE, STDOUT
import sys

parser = argparse.ArgumentParser(description='HouseKeeper keeps your house clean')

parser.add_argument('job', metavar='JOB', type=str, nargs='*')
parser.add_argument('-n', "--noop", action="store_true")
parser.add_argument('-r', "--run", action="store_true")
parser.add_argument('-s', "--silent", action="store_true")
parser.add_argument('-v', "--verbose", action="store_true")
parser.add_argument('-c', "--config", action="store")

args = parser.parse_args()

import logging
logger = logging.getLogger()
sh = logging.StreamHandler(sys.stdout)
sh.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(name)-12s %(message)s", datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(sh)
logger.setLevel(logging.WARNING)
if args.verbose:
    logger.setLevel(logging.DEBUG)

CONFIG_DIR = "/etc/housekeeper"
CONFIG_FILE = None

if args.config:
    if isdir(args.config):
        CONFIG_DIR = args.config
    elif isfile(args.config) or islink(args.config):
        CONFIG_DIR = None
        CONFIG_FILE = args.config
    else:
        print("Invalid config argument '%s', must be a file or directory" % args.config)
        sys.exit(1)

NOOP = True

if args.run:
    NOOP = False


def output(text):
    if args.silent:
        return

    print(text)

class Job(object):
    """
    """
    DEFAULT_CONFIG = {}

    def __init__(self, name, config):
        self.name = name
        self.config = config

    def execute(self):
        """
        """

    def noop(self):
        """
        """

class FindRemoveJob(Job):
    """
    """
    PARAMETERS = ["depth", "match", "older", "recurse", "root"]

    DEFAULT_CONFIG = {"recurse": False}

    def __init__(self, *args, **kwargs):
        super(FindRemoveJob, self).__init__(*args, **kwargs)

        self.roots = []

        try:
            root_expression = self.config["root"]
        except KeyError:
            raise RuntimeError("%s: field 'root' needs to be defined" % self.name)

        if "*" in root_expression:
            self.roots = glob(root_expression)
        else:
            self.roots = [root_expression]

        self.roots = [r.rstrip("/") for r in self.roots]
        self.roots.sort()

        for root in self.roots:
            if not isdir(root):
                raise RuntimeError("%s: root %s needs to be an existing directory" % (self.name, root))

        if type(self.config["recurse"]) == str:
            self.config["recurse"] = eval(self.config["recurse"])

    def execute(self):
        """
        :return:
        """
        for root in self.roots:
            cmd = self.generate_find_command(root)
            cmd.append("-delete")

            output("%s: execute command: %s (do not copy-paste this command)" % (self.name, " ".join(cmd)))

            popen = Popen(cmd, stdout=PIPE, stderr=STDOUT)
            popen.communicate()

    def noop(self):
        """

        :return:
        """
        for root in self.roots:
            cmd = self.generate_find_command(root)

            if NOOP:
                output("%s: execute command: %s" % (self.name, " ".join(cmd)))

            popen = Popen(cmd, stdout=PIPE, stderr=STDOUT)
            out, _ = popen.communicate()

            for line in out.splitlines():
                output("%s: would remove: %s" % (self.name, line))

    def generate_find_command(self, root, type="f"):
        """
        """
        if not "match" in self.config and not "older" in self.config:
            raise RuntimeError("either 'match' or 'older' needs to be defined")

        cmd = ["find", root]

        # maxdepth
        if "depth" in self.config:
            cmd += ["-maxdepth", self.config.get("depth", self.config["depth"])]
        elif "recurse" in self.config:
            if self.config["recurse"] is False:
                cmd += ["-maxdepth", self.config.get("depth", "1")]

        # type
        if type:
            assert type in ["f", "d", "l"]
            cmd += ["-type", type]

        # name
        if "match" in self.config:
            cmd += ["-name", self.config["match"]]

        # mtime
        if "older" in self.config:
            prefix = "+"
            context = self.config["older"]

            if context.endswith("d"):
                context = context[:-1]
            elif context.endswith("w"):
                context = int(context[:-1]) * 7
            elif context.endswith("m"):
                context = int(context[:-1]) * 30
            elif context.endswith("y"):
                context = int(context[:-1]) * 365

            cmd += ["-mtime", "%s%s" % (prefix, context)]

        return cmd

class Keep(FindRemoveJob):
    """
    Keeps <keep> amount of files (newest ones)
    """
    PARAMETERS = ["depth", "match", "older", "recurse", "root", "keep"]

    def get_file_list(self, root):
        cmd = self.generate_find_command(root)

        if NOOP:
            output("%s: execute command: %s" % (self.name, " ".join(cmd)))

        popen = Popen(cmd, stdout=PIPE, stderr=STDOUT)
        out, _ = popen.communicate()

        if popen.returncode == 0:
            return out.splitlines()

    def get_files_to_consider(self):
        
        consider_list = []
        
        for root in self.roots:
            file_list = self.get_file_list(root)

            order = []

            for file in file_list:
                order.append((os.stat(file).st_mtime, file))

            order.sort()

            keep = int(self.config["keep"])

            order = order[:-keep]

            consider_list += [o[1] for o in order]
        
        return consider_list
    
    def execute(self):
        """

        :return:
        """
        file_list = self.get_files_to_consider()

        for f in file_list:
            if isfile(f):
                os.remove(f)

    def noop(self):
        file_list = self.get_files_to_consider()

        for f in file_list:
            output("%s: would remove: %s" % (self.name, f))

JOB_TYPE_MAPPING = {
    "find-remove": FindRemoveJob,
    "keep": Keep
}

class HouseKeeper(object):

    def __init__(self):
        """

        :return:
        """
        self.config = {}
        self.read_config()

    def read_config(self):
        """

        :return:
        """
        if CONFIG_DIR:
            logger.debug("Looking for config files at %s" % CONFIG_DIR)
            config_files = glob(join(CONFIG_DIR, "*"))
            logger.debug("Found %s config files" % len(config_files))
        else:
            config_files = [CONFIG_FILE]

        for file in config_files:
            if not isfile(file):
                logger.debug("Config file '%s' is not a file, ignoring it" % file)
                continue

            if file.endswith("~"):
                logger.debug("Ignore config file '%s'" % file)
                continue

            if file.endswith(".yaml"):
                self._read_config_file_yaml(file)
            elif file.endswith(".ini"):
                self._read_config_file_ini(file)
            else:
                output("unrecognized config file %s" % file)

    def _read_config_file_yaml(self, path):
        """

        :param path:
        :return:
        """
        import yaml
        f = open(path)
        c = yaml.load(f)
        f.close()

        self.config.update(c)

    def _read_config_file_ini(self, path):
        """

        :param path:
        :return:
        """
        logger.info("Reading config file %s" % path)
        def as_dict(config):
            """
            Converts a ConfigParser object into a dictionary.

            The resulting dictionary has sections as keys which point to a dict of the
            sections options as key => value pairs.
            """
            the_dict = {}
            for section in config.sections():
                the_dict[section] = {}
                for key, val in config.items(section):
                    the_dict[section][key] = val
            return the_dict

        if sys.version_info[0] == 2:
            from ConfigParser import ConfigParser
        else:
            from configparser import ConfigParser

        config = ConfigParser()
        config.read(path)

        self.config.update(as_dict(config))

    def start(self):
        """

        :return:
        """
        if not self.config:
            output("No configuration loaded, exiting")
            sys.exit(0)

        for job, job_config in self.config.items():
            job_type = job_config.get("type", "find-remove")

            # determine job class
            try:
                job_class = JOB_TYPE_MAPPING.get(job_type)
            except KeyError:
                raise RuntimeError("%s: no such type definition: '%s'" % (job, job_type))

            # default config
            if hasattr(job_class, "DEFAULT_CONFIG"):
                new_config = deepcopy(job_class.DEFAULT_CONFIG)
                new_config.update(job_config)
                job_config = new_config

            # validate configuration parameters
            job_parameter_names = job_config.keys()
            try:
                job_parameter_names.remove("type")
            except ValueError:
                pass
            for job_parameter_name in job_parameter_names:
                if not job_parameter_name in job_class.PARAMETERS:
                    raise RuntimeError("%s: invalid field '%s' in job definition for job class %s" % (job, job_parameter_name, job_class.__name__))

            job_instance = job_class(job, job_config)

            if NOOP:
                output("Executing job %s (noop)" % job)
                job_instance.noop()
            else:
                output("Executing job %s" % job)
                job_instance.execute()

if __name__ == "__main__":
    h = HouseKeeper()
    h.start()
