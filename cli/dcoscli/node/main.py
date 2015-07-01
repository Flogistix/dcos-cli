"""Manage DCOS nodes

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

import os
import subprocess

import dcoscli
import docopt
from dcos import cmds, emitting, errors, mesos, util
from dcos.errors import DCOSException
from dcoscli import tables

logger = util.get_logger(__name__)
emitter = emitting.FlatEmitter()


def main():
    try:
        return _main()
    except DCOSException as e:
        emitter.publish(e)
        return 1


def _main():
    util.configure_logger_from_environ()

    args = docopt.docopt(
        __doc__,
        version="dcos-node version {}".format(dcoscli.version))

    return cmds.execute(_cmds(), args)


def _cmds():
    """
    :returns: All of the supported commands
    :rtype: [Command]
    """

    return [
        cmds.Command(
            hierarchy=['node', '--info'],
            arg_keys=[],
            function=_info),

        cmds.Command(
            hierarchy=['node', 'ssh'],
            arg_keys=['--master', '--slave', '--option', '--config_file',
                      '--user'],
            function=_ssh),

        cmds.Command(
            hierarchy=['node'],
            arg_keys=['--json'],
            function=_list),
    ]


def _info():
    """Print node cli information.

    :returns: process return code
    :rtype: int
    """

    emitter.publish(__doc__.split('\n')[0])
    return 0


def _list(json_):
    """List DCOS nodes

    :param json_: If true, output json.
        Otherwise, output a human readable table.
    :type json_: bool
    :returns: process return code
    :rtype: int
    """

    client = mesos.DCOSClient()
    slaves = client.get_state_summary()['slaves']
    if json_:
        emitter.publish(slaves)
    else:
        table = tables.slave_table(slaves)
        output = str(table)
        if output:
            emitter.publish(output)
        else:
            emitter.publish(errors.DefaultError('No slaves found.'))


def _ssh(master, slave, option, config_file, user):
    """SSH into a DCOS node.  Since only the masters are definitely
    publicly available, we first ssh into an arbitrary master, then
    hop to the desired node.

    :param master: True if we ssh into the master
    :type master: bool
    :param slave: The slave ID to ssh into
    :type slave: str
    :param option: SSH option
    :type option: str
    :param config_file: SSH config file
    :type config_file: str
    :param user: SSH user
    :type user: str
    :rtype: int
    :returns: process return code
    """
    if not os.environ.get('SSH_AUTH_SOCK'):
        raise DCOSException(
            "There is no SSH_AUTH_SOCK env variable, which likely means you " +
            "aren't running `ssh-agent`.  `dcos node ssh` depends on " +
            "`ssh-agent` so we can safely use your private key to hop " +
            "between nodes in your cluster.  Please run `ssh-agent`, " +
            "then add your private key with `ssh-add`.")

    master_public_ip = mesos.DCOSClient().metadata()['PUBLIC_IPV4']
    ssh_options = ' '.join('-o {}'.format(opt) for opt in option)

    if config_file:
        ssh_config = '-F {}'.format(config_file)
    else:
        ssh_config = ''

    if master:
        host = 'leader.mesos'
    else:
        summary = mesos.DCOSClient().get_state_summary()
        slave_obj = None
        for slave_ in summary['slaves']:
            if slave_['id'] == slave:
                slave_obj = slave_
                break
        if slave_obj:
            host = mesos.parse_pid(slave_obj['pid'])[1]
        else:
            raise DCOSException('No slave found with ID [{}]'.format(slave))

    cmd = "ssh -A -t {0} {1} {2}@{3} ssh -A -t {2}@{4}".format(
        ssh_options,
        ssh_config,
        user,
        master_public_ip,
        host)

    return subprocess.call(cmd, shell=True)
