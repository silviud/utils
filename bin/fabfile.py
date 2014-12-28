from fabric.api import *
import boto


def prod():
    # TODO - connect to find hosts in account by tags or use DNS
    env.roledefs = {
            'web': ['ec2-23-21-155-88.compute-1.amazonaws.com', 
                    'ec2-23-21-149-232.compute-1.amazonaws.com',
                    'ec2-23-21-142-242.compute-1.amazonaws.com'
                ],
            'zabbix': ['ec2-54-146-97-28.compute-1.amazonaws.com'],
            'admin': ['admin.icastpro.ca']
            }
    env.user = 'ec2-user'
    env.disable_known_hosts = True  # default
    env.reject_unknown_hosts = False # -o 'CheckHostIP=no' -o 'StrictHostKeyChecking=no' 


@roles('web')
def reset_nohup():
    require('roledefs', provided_by=[prod])   
    with cd('/home/ec2-user/sync'):
        sudo('echo > nohup.out')
    sudo("df -h")
