import json
import os
import pty
import subprocess
import time

import dcos.util as util
from dcos import mesos
from dcos.util import create_schema

from ..fixtures.node import slave_fixture
from .common import assert_command, exec_command


def test_help():
    stdout = b"""Manage DCOS nodes

Usage:
    dcos node --info
    dcos node [--json]
    dcos node ssh [--option SSHOPT=VAL ...]
                  [--config_file=<path>]
                  [--user=<user>]
                  (--master | --slave=<slave-id>)

Options:
    -h, --help              Show this screen
    --info                  Show a short description of this subcommand
    --json                  Print json-formatted nodes
    --master                SSH into the leading master node
    --slave=<slave-id>      SSH into this slave node
    --option SSHOPT=VAL     SSH option (see `man ssh_config`)
    --config_file=<path>    Path to ssh config file
    --user=<user>           SSH user [default: core]
    --version               Show version
"""
    assert_command(['dcos', 'node', '--help'], stdout=stdout)


def test_info():
    stdout = b"Manage DCOS nodes\n"
    assert_command(['dcos', 'node', '--info'], stdout=stdout)


def test_node():
    returncode, stdout, stderr = exec_command(['dcos', 'node', '--json'])

    assert returncode == 0
    assert stderr == b''

    nodes = json.loads(stdout.decode('utf-8'))
    schema = _get_schema(slave_fixture())
    for node in nodes:
        assert not util.validate_json(node, schema)


def test_node_table():
    returncode, stdout, stderr = exec_command(['dcos', 'node'])

    assert returncode == 0
    assert stderr == b''
    assert len(stdout.decode('utf-8').split('\n')) > 2


def test_node_ssh_master():
    _node_ssh(['--master'])


def test_node_ssh_slave():
    slave_id = mesos.DCOSClient().get_state_summary()['slaves'][0]['id']
    _node_ssh(['--slave={}'.format(slave_id)])


def test_node_ssh_option():
    stdout, stderr = _node_ssh_output(
        ['--master', '--option', 'Protocol=0'])
    assert stdout == b''
    assert stderr.startswith(b'ignoring bad proto spec')


def test_node_ssh_config_file():
    stdout, stderr = _node_ssh_output(
        ['--master', '--config_file', 'tests/data/node/ssh_config'])
    assert stdout == b''
    assert stderr.startswith(b'ignoring bad proto spec')


def test_node_ssh_user():
    stdout, stderr = _node_ssh_output(
        ['--master', '--user=bogus', '--option', 'PasswordAuthentication=no'])
    assert stdout == b''
    assert stderr.startswith(b'Permission denied')


def _node_ssh_output(args):
    # ssh must run with stdin attached to a tty
    master, slave = pty.openpty()
    proc = subprocess.Popen(['dcos', 'node', 'ssh'] + args,
                            stdin=slave,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            preexec_fn=os.setsid,
                            close_fds=True)
    os.close(slave)

    # wait for the ssh connection
    time.sleep(3)

    # kill the whole process group
    os.killpg(os.getpgid(proc.pid), 15)

    os.close(master)
    return proc.communicate()


def _node_ssh(args):
    stdout, stderr = _node_ssh_output(args)
    assert stdout
    assert stderr == b''


def _get_schema(slave):
    schema = create_schema(slave)
    schema['properties']['used_resources']['required'].remove('ports')
    schema['properties']['offered_resources']['required'].remove('ports')
    schema['properties']['attributes']['additionalProperties'] = True

    return schema
