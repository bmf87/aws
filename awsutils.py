import boto3


# Get session resource for API calls
# Default service: ec2
def authenticate(region, creds, service='ec2'):
    aws_pricing_region = "us-east-1"

    # if credentials were specified in arguments (-k and -i options)
    if creds['aws_access_key_id'] and creds['aws_secret_access_key']:
        session = boto3.session.Session(
            aws_access_key_id=creds['aws_access_key_id'],
            aws_secret_access_key=creds['aws_secret_access_key'])
    # if not using specified profile - "default" gets used
    else:
        session = boto3.session.Session(profile_name=creds['profile'])
        # Return resource for AWS API
        resource = session.resource(service, region_name=region)
        pricing_client = session.client('pricing', region_name=aws_pricing_region)

    return resource, pricing_client, session

def getEC2Objects(region):
    #boto3.set_stream_logger('')
    session = boto3.Session(region_name=region)
    credentials = session.get_credentials().get_frozen_credentials()

    secrets = "Access Key: {0}\nSecret Key: {1}\nToken: {2}\n".format(
                                credentials.access_key, credentials.secret_key, credentials.token)
    #print(secrets)
    ec2_resource = session.resource('ec2', region_name=region)

    return session, ec2_resource


def getSTSClient(account_numb, region, role):

    try:
        sts_client = boto3.client('sts')

        assumedRoleObj = sts_client.assume_role(
            RoleArn="arn:aws:iam::" + account_numb + ":role/" + role,
            RoleSessionName="EBSConvertSession"
        )

        credentials = assumedRoleObj['Credentials']

        _client = boto3.client(
            'ec2',
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'],
            region_name=region
        )
    except Exception as ex:
        print(ex)
        raise

    return _client


# Convert AWS tags data struct into a key/value hash
def tags_to_map(resource):
    tag_hash = {}
    if resource.tags is None:
        return tag_hash
    for rtag in resource.tags:
        tag_hash[rtag['Key']] = rtag['Value']

    return tag_hash

# Get all AWS regions where service exists
# Default service: uses EC2 service
def get_regions(creds, service='ec2'):
    region_list = []

    # if credentials were args with -k and -i option use them to authenticate
    if creds['aws_access_key_id'] and creds['aws_secret_access_key']:
        session = boto3.session.Session(
            aws_access_key_id=creds['aws_access_key_id'],
            aws_secret_access_key=creds['aws_secret_access_key'])
    # if not use specified profile or use "default" if not declared
    else:
        session = boto3.session.Session(profile_name=creds['profile'])

    ec2 = session.client(service)
    region_dict = ec2.describe_regions()
    for region_item in region_dict['Regions']:
        region_list.append(region_item['RegionName'])

    return region_list


# Overloaded method to get all EC2 regions
# Param: Using the boto3 Session obj
def get_regions(session):
    region_list = []

    ec2 = session.client('ec2')
    region_dict = ec2.describe_regions()
    for region_item in region_dict['Regions']:
        region_list.append(region_item['RegionName'])

    return region_list


# Obtain current AWS Account Number
def get_account_number():
    stsClient = boto3.client('sts')

    return stsClient.get_caller_identity()['Account']


# Resolve a region code (eu-west-1) to region name
# Why? AWS Pricing API does not use region codes
def resolve_region(region):
    aws_region_map = {
        'ca-central-1': 'Canada (Central)',
        'ap-northeast-3': 'Asia Pacific (Osaka-Local)',
        'us-east-1': 'US East (N. Virginia)',
        'ap-northeast-2': 'Asia Pacific (Seoul)',
        'us-gov-west-1': 'AWS GovCloud (US)',
        'us-east-2': 'US East (Ohio)',
        'ap-northeast-1': 'Asia Pacific (Tokyo)',
        'ap-south-1': 'Asia Pacific (Mumbai)',
        'ap-southeast-2': 'Asia Pacific (Sydney)',
        'ap-southeast-1': 'Asia Pacific (Singapore)',
        'sa-east-1': 'South America (Sao Paulo)',
        'us-west-2': 'US West (Oregon)',
        'eu-west-1': 'EU (Ireland)',
        'eu-west-3': 'EU (Paris)',
        'eu-west-2': 'EU (London)',
        'us-west-1': 'US West (N. California)',
        'eu-central-1': 'EU (Frankfurt)',
        'eu-north-1': 'EU (Stockholm)'
    }

    return aws_region_map[region]