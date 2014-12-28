from fabric.api import *
from boto.ec2 import connect_to_region
import os


def _make_connection(region):
    conn = connect_to_region(
        region_name = region, 
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"), 
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY")
    )
    return conn

def _inventory_from_tag(region, tag='', value="*"):
    """
    :params region: string as in ec2-east-1 ...
    :params tag: TODO find if is a sg or not and place it down the filter - can be a list
      that contains {group-id: sg-xxx} and so on
    :params value: list or sring with the identifier
    :returns: list of dns public names
    """
    public_dns   = []
    connection   = _make_connection(region)
    if tag.startswith('group-'):
        key = "group-name"
    else:
        key = "tag:" + tag

    reservations = connection.get_all_instances(filters = {key : value})
    for reservation in reservations:
        for instance in reservation.instances:
            if instance.state == 'running':
                print "Adding instance", instance.public_dns_name
                public_dns.append(str(instance.public_dns_name))
    return public_dns

def prod(key='class', value='monitoring', region='us-east-1'):
    # TODO - connect to find hosts in account by tags or use DNS
    #        'web': ['ec2-23-21-155-88.compute-1.amazonaws.com', 
    #                'ec2-23-21-149-232.compute-1.amazonaws.com',
    #                'ec2-23-21-142-242.compute-1.amazonaws.com'
    #            ],
    """
    :params region: string as in ec2-east-1
    :params key: string representating the Key portion of a ec2 tag e.g. Role, Name, class 
        or sg-group representating a security group e.g. sg-group
    :params value: string value for tag or security group
    Example:
        fab prod:key=sg-group,value=MySG func_to_call
    """
    web = _inventory_from_tag(region=region, tag=key, value=value)

    env.roledefs = {
            'zabbix': ['ec2-54-146-97-28.compute-1.amazonaws.com'],
            'admin': ['admin.icastpro.ca'],
            'web': web
            }
    env.user = 'ec2-user'
    env.disable_known_hosts = True  # default
    env.reject_unknown_hosts = False # -o 'CheckHostIP=no' -o 'StrictHostKeyChecking=no' 


@roles('web')
def time():
    run('date')


@roles('web')
def reset_nohup():
    require('roledefs', provided_by=[prod])   
    with cd('/home/ec2-user/sync'):
        sudo('echo > nohup.out')
    sudo("df -h")
