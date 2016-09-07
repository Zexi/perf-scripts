#!/usr/bin/env python

from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase

OPTIONS = namedtuple(
    'Options', [
        'listtags', 'listtasks', 'listhosts', 'syntax', 'connection','module_path',
        'forks', 'remote_user', 'private_key_file', 'ssh_common_args', 'ssh_extra_args',
        'sftp_extra_args', 'scp_extra_args', 'become', 'become_method', 'become_user',
        'verbosity', 'check'
    ]
)

DEFAULT_OPTIONS = OPTIONS(
            listtags=False, listtasks=False, listhosts=False, syntax=False, connection='ssh',
            module_path='', forks=100,
            remote_user='root', private_key_file=None, ssh_common_args=None, ssh_extra_args=None,
            sftp_extra_args=None, scp_extra_args=None, become=False, become_method=None, become_user='root',
            verbosity=None, check=False
        )


class ResultCallback(CallbackBase):
    def v2_runner_on_ok(self, result, **kwargs):
        host = result._host
        self.task_obj.return_results = {host.name: result._result}


class AnsibleTask(object):

    def __init__(self, hosts='127.0.0.1', module='shell', args='ls -l',
                 options=DEFAULT_OPTIONS, name='Ansible Play'):
        self.hosts = hosts
        self.module = module
        self.args = args
        self.options = options
        self.name = name
        self.task = dict(action=dict(
            module=self.module, args=self.args
        ), register='shell_out')
        self.tasks = [self.task]
        # initialize needed objects
        self.variable_manager = VariableManager()
        self.loader = DataLoader()
        self.passwords = dict()
        self.inventory = Inventory(loader=self.loader, variable_manager=self.variable_manager, host_list=[self.hosts])
        self.variable_manager.set_inventory(self.inventory)
        self.play_source = dict(
            name=self.name, hosts=self.hosts,
            gather_facts='no', tasks=self.tasks
        )
        self.play = Play().load(self.play_source, loader=self.loader,
                                variable_manager=self.variable_manager)
        self.results_callback = ResultCallback()
        self.return_results = {}
        setattr(self.results_callback, 'task_obj', self)

    def ansible_play(self):
        # run it
        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.options,
                passwords=self.passwords,
                stdout_callback=self.results_callback,
                # stdout_callback='default',
            )
            result = tqm.run(self.play)
        finally:
            if tqm is not None:
                tqm.cleanup()
                #self.inventory.clear_pattern_cache()
            if result != 0:
                raise ValueError('SSH Command Failed, resturn: %s' % result)
            return self.return_results

if __name__ == '__main__':
    test_option = OPTIONS(
                listtags=False, listtasks=False, listhosts=False, syntax=False, connection='ssh',
                module_path='', forks=100,
                remote_user='root', private_key_file='/Users/lzx/Tools/perf-scripts/pst_ssh_prikey', ssh_common_args=None, ssh_extra_args=None,
                sftp_extra_args=None, scp_extra_args=None, become=False, become_method=None, become_user='root',
                verbosity=None, check=False
            )

    test_task = AnsibleTask('192.168.59.104', options=test_option)
    test_task.ansible_play()
