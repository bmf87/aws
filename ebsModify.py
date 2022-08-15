import logging
import os
import datetime
from datetime import date
from utils import argument_parser
from awsutils \
    import tags_to_map, getEC2Objects, get_account_number

#############################
# Constants
#############################
CONST_INFO = 'INFO'
CONST_WARNING = 'WARNING'
CONST_ERROR = 'ERROR'
CONST_CRITICAL = 'CRITICAL'

#############################
# Logger
#############################
logging.basicConfig(filename=os.getcwd() + "/logs/ebsModify_" + str(date.today()) + ".log",
                    format='%(asctime)s %(message)s',
                    filemode='w')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


#############################
# Functions
#############################

# Get EC2 Instance by Id
def getEc2_byId(auth, instanceId):

    # Fetch non-terminated EC2 instances
    instance = auth.Instance(instanceId)

    return instance

# Get EC2 Instance by Tag:Name=hostname
def getEc2_byName(ec2, hostname):

    instanceList = list(ec2.instances.filter(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [
                    hostname
                ]
            }
        ]
    ))

    # Multiple Tag Values?
    if len(instanceList) > 1:
        warning_message = 'Multiple EC2 instances found with ' + hostname \
                          + ' using the last one'
        record_message(warning_message, CONST_WARNING)

    return instanceList.pop()


def gp3_convert(session, vol_id):
    response = None

    try:
        # Requires low-level API call
        client = session.client('ec2')
        response = client.modify_volume(VolumeId=vol_id, VolumeType='gp3')
    except Exception as e:
        exception_message = "ERROR converting EBS volume id " + vol_id + " to gp3" \
                            + " error message: " + str(e)
        record_message(exception_message, CONST_CRITICAL)

    return response


def take_snap(ec2, volmap):
    snapshot = None

    try:
        snapshot = ec2.create_snapshot(
            VolumeId=volmap['volume.id'],
            Description='Created for ' + volmap['ec2.name'] + ' - ' + volmap['volume.device'],
            TagSpecifications=[
                {
                    'ResourceType': 'snapshot',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': 'gp3-convert-' + volmap['volume.id']
                        },
                        {
                            'Key': 'CostCenterID',
                            'Value': volmap['costCenter']
                        },
                        {
                            'Key': 'CreatedDate',
                            'Value': str(date.today())
                        },
                        {
                            'Key': 'TTL',
                            'Value': '20'
                        }

                    ]

                },
            ]

        )

        # Block until snap is done!
        snapshot.wait_until_completed()

    except Exception as e:
        exception_message = "ERROR creating snapshot for EBS volume id " + volmap['volume.id'] \
                            + " error message: " + str(e)

        record_message(exception_message, CONST_CRITICAL)

    return snapshot.id


def record_message(message, level):
    print(message)

    if level == CONST_INFO:
        logger.info(message)
    elif level == CONST_WARNING:
        logger.warning(message)
    elif level == CONST_ERROR:
        logger.error(message)
    elif level == CONST_CRITICAL:
        logger.critical(message)


def main():
    credentials, params, verbose_mode = argument_parser()
    resource_file = params['file']
    region = params['region']

    # Dev Runs
    #ec2_res, price_client, aws_session = authenticate(region, credentials)

    # Server Runs
    aws_session, ec2_res = getEC2Objects(region)
    aws_account = get_account_number()

    message = "[STARTING] EBS Modification job from account: %s at %s" % (aws_account, str(datetime.datetime.now().astimezone()))
    record_message(message, CONST_INFO)

    with open(resource_file, 'r') as f:
        ec2Counter = 0
        for line in f:
            cleanLine = line.strip()
            # No newLine chars
            if cleanLine:
                hostname = cleanLine
                ec2Counter += 1
                start = "%s] Processing EBS volumes for EC2 --> %s" % (str(ec2Counter), hostname)
                record_message(start, CONST_INFO)


                ec2_instance = getEc2_byName(ec2_res, hostname)
                tags = tags_to_map(ec2_instance)
                volume_list = []

                ec2_name = 'EC2 Name: ' + tags['Name']
                record_message(ec2_name, CONST_INFO)
                cc = 'EC2 CostCenterID: ' + tags['CostCenterID']
                record_message(cc, CONST_INFO)

                volumes = ec2_instance.volumes.all()
                # Convert all EBS Volumes
                for volume in volumes:
                    # Ensure volume in-scope convertible volume_type == gp2
                    if volume.volume_type == 'gp2':
                        device_name = volume.attachments[0][u'Device']
                        volume_list.append({
                            'ec2.name': tags['Name'],
                            'costCenter': tags['CostCenterID'],
                            'volume.device': device_name,
                            'volume.id': volume.id,
                            'volume.volume_type': volume.volume_type,
                            'volume.size': volume.size,
                            'volume.create_time': volume.create_time

                        })
                        ec2_vol_info = "Id: {0}\nVolume Name: {1}\nVolume Type: {2}\nVolume Size: {3}\nVolume Create Time: {4}\n".format(
                                volume.id, device_name, volume.volume_type, volume.size, volume.create_time)

                        record_message(ec2_vol_info, CONST_INFO)

                        volmap = volume_list.pop(0)
                        snapshot_id = take_snap(ec2_res, volmap)

                        # Ensure snapshot Id to proceed
                        if (len(snapshot_id)):
                            response = gp3_convert(aws_session, volmap['volume.id'])

                            mod_map = response['VolumeModification']
                            volumeId = mod_map['VolumeId']
                            mod_state = mod_map['ModificationState']
                            size = str(mod_map['TargetSize'])
                            mod_volumeType = mod_map['TargetVolumeType']

                        ec2_vol_modinfo = "VolumeId: {0}\nModificationState: {1}\nTargetSize: {2}\nTargetVolumeType: {3}\n".format(
                                  volumeId, mod_state, size, mod_volumeType)

                        record_message(ec2_vol_modinfo, CONST_INFO)

                        #for k, v in response.items():
                        #    print(k, v)
                    else:
                        ec2_vol_info = volume.id + ' is not an in-scope volume_type for converting --> volume_type=[' + volume.volume_type + ']'
                        record_message(ec2_vol_info, CONST_INFO)

    message = "[ENDING] EBS Modification job at %s" % (str(datetime.datetime.now().astimezone()))
    record_message(message, CONST_INFO)


if __name__ == "__main__":
    main()