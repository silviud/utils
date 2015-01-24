from fabric.api import *
from fabric.contrib.project import rsync_project
from fabric.contrib.files import upload_template

from boto.ec2 import connect_to_region
import os


RSYNC_EXCLUDE = [
    '*.swp',
    '*.pyc',
    "#*#",
    ".git"
]


def _make_connection(region):
    """
    :params region: the aws region to connect
    :returns connection:
    """
    conn = connect_to_region(
        region_name=region,
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
    public_dns = []
    connection = _make_connection(region)
    if tag.startswith('group-'):
        key = "group-name"
    else:
        key = "tag:" + tag

    reservations = connection.get_all_instances(filters={key : value})
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
        fab prod:key=group-name,value=MySG reset_nohup
    """
    web = _inventory_from_tag(region=region, tag=key, value=value)

    env.roledefs = {'zabbix': ['ec2-54-146-97-28.compute-1.amazonaws.com'],
                    'admin': ['admin.icastpro.ca'],
                    'web': web}
    env.user = 'ec2-user'
    # env.roledefs = {'web': ['192.168.50.10']}
    # env.user = 'vagrant'
    env.disable_known_hosts = True  # default
    env.reject_unknown_hosts = False # -o 'CheckHostIP=no' -o 'StrictHostKeyChecking=no'
    env.site_cookbook = 'app_prod'
    env.chef_repo = '/var/chef/chef-repo'
    env.chef_conf = '/var/chef/chef-repo/conf/solo.rb'


@roles('web')
def time():
    """ date func """
    run('date')


@roles('web')
def reset_nohup():
    """ resets the nohup file used by sync """
    require('roledefs', provided_by=[prod])
    with settings(warn_only=True):
        with cd('/home/ec2-user/sync'):
            sudo('echo > nohup.out')
    sudo("df -h")


@roles('web')
def bootstrap_chef():
    """ install chef on the remote """
    sudo("mkdir -p %s" % env.chef_repo)
    sudo("chown -R %s: %s" % (env.user, env.chef_repo))
    sudo("curl -L https://www.chef.io/chef/install.sh | sudo bash") 


@roles('web')
def run_chef(whyrun=False):
    """ 
    :params whyrun: dry run with chef (not acctually running)
    """
    with lcd("chef"):
        local("berks vendor -b site-cookbooks/%s/Berksfile" % env.site_cookbook)
    sudo("chown -R %s: %s" % (env.user, env.chef_repo))
    # / at the end of a dir means will sync the contents of the dir not the dir
    rsync_project(local_dir='chef/berks-cookbooks/',
                  remote_dir="%s/%s" % (env.chef_repo, 'cookbooks'),
                  exclude=RSYNC_EXCLUDE)
    rsync_project(local_dir='chef/cookbooks/',
                  remote_dir="%s/%s" % (env.chef_repo, 'cookbooks'),
                  exclude=RSYNC_EXCLUDE)
    rsync_project(local_dir='chef/site-cookbooks/',
                  remote_dir="%s/%s" % (env.chef_repo, 'cookbooks'),
                  exclude=RSYNC_EXCLUDE)
    rsync_project(local_dir='chef/conf',
                  remote_dir="%s" % env.chef_repo,
                  exclude=RSYNC_EXCLUDE)
    sudo("chef-solo -c %s -o %s" % (env.chef_conf, env.site_cookbook))

