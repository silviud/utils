from boto.ec2 import connect_to_region
import os


def make_connection(region):
    conn = connect_to_region(
        region_name = region, 
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"), 
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY")
    )
    return conn

def inventory_from_tag(region, tag='class', value="*"):
    """
    :params region: string as in ec2-east-1 ...
    :params tag: TODO find if is a sg or not and place it down the filter - can be a list
      that contains {group-id: sg-xxx} and so on
    :params value: list or sring with the identifier
    :returns: list of dns public names
    """
    public_dns   = []
    connection   = make_connection(region)
    key = "tag:" + tag
    reservations = connection.get_all_instances(filters = {key : value})
    for reservation in reservations:
        for instance in reservation.instances:
            print "Instance", instance.public_dns_name
            public_dns.append(str(instance.public_dns_name))
    return public_dns


if __name__ == '__main__':
    print "Getting hosts by tag iCastPro"
    print inventory_from_tag('us-east-1', value='monitoring')

