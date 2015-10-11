#!/usr/bin/env python
#
# A dead simple process manager
#
# What happens?
#  - parses configuration file
#  - starts all programs in order they are defined in the config
#  - waits for sigterm
#  - stop all programs when sigterm is recieved
#
# ConfigParser uses OrderedDict therefore programs will be started / stopped in
# the order they are defined in the config

import argparse
import signal
import sys
import ConfigParser
import re
import os
import subprocess
import logging
from collections import OrderedDict

SIGNAL_NAMES=dict((k, v) for v, k in reversed(sorted(signal.__dict__.items())) if v.startswith('SIG') and not v.startswith('SIG_'))

PROGRAMS = OrderedDict()

def parse_config(config_file):
    config = ConfigParser.ConfigParser()
    config.read(config_file)

    sections = config._sections
    global PROGRAMS

    for key,value in sections.iteritems():
        if not re.match('^program:', key):
            continue

        env = os.environ
        try:
            environment = value['environment'].split(',')
        except KeyError:
            environment = []
        else:
            for item in environment:
                key2, value2 = item.split('=')
                value2 = value2.strip()
                env[key2] = value2

        cmd_start = value['start'].split()
        cmd_stop = value['stop'].split()

        PROGRAMS[key] = {'cmd_start':cmd_start, 'cmd_stop':cmd_stop, 'env':env}

    return

def call_cmd(cmd, env):

    logger = logging.getLogger()
    logger.info("exec '{0}'".format(' '.join(cmd)))
    proc = subprocess.Popen(cmd, env=env)
    rv = proc.wait()
    logger.info('\'{0}\' returned {1}'.format(' '.join(cmd), rv))

    return rv

def start_all():
    logger = logging.getLogger()
    for k, v in PROGRAMS.iteritems():
        rv = call_cmd(v['cmd_start'], v['env'])

        if rv != 0:
            logger.error("start failed for {0}".format(k))
            sys.exit(rv)

    return

def stop_all():
    logger = logging.getLogger()
    rev_progs = reversed([ (k, v) for k, v in PROGRAMS.iteritems() ])

    fail_stop = False
    for k, v in rev_progs:
        rv = call_cmd(v['cmd_stop'], v['env'])

        if rv != 0:
            fail_stop = True
            logger.warn("stop failed for {0}".format(k))

    if fail_stop:
        return 1

    return 0

def signal_handler(signal, frame):
    logger = logging.getLogger()
    logger.info('Caught Signal {0}'.format(SIGNAL_NAMES[signal]))

    if signal in [15]:
        sys.exit(stop_all())

    return

def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()

    parser = argparse.ArgumentParser(description="Run startup commands. Wait for SIGTERM. Run shutdown commands.")
    parser.add_argument('-c', '--config', help="configuration file" )
    args = parser.parse_args()

    config_file = args.config
    if config_file and not os.path.isfile(config_file):
        logger.error('no such file: {0}'.format(config_file))
        sys.exit(1)
    elif not config_file:
        cwd_config = os.path.join(os.getcwd(), 'waiter.conf')
        if os.path.isfile(cwd_config):
            config_file = cwd_config
        else:
            logger.error('unable to find waiter.conf in cwd and option not passed')
            sys.exit(1)

    parse_config(config_file)

    signal.signal(signal.SIGTERM, signal_handler)

    # Starts processes
    start_all()

    logger.info('waiting for SIGTERM...')
    while True:
        signal.pause()

    return

if __name__ == "__main__":
    main()
