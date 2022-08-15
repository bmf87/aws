import argparse


# Command line argument parsing code
def argument_parser():
    aws_id = None
    aws_secret_key = None
    parser = argparse.ArgumentParser(
        description='Utils argument parser')
    # Provide support for authentication using custom or default AWS profile
    parser.add_argument(
        '-p',
        '--profile',
        default='default',
        help='default AWS profile is used if one is not specified')
    # Provide support for custom or default AWS region
    parser.add_argument(
        '-r',
        '--region',
        default='us-east-1',
        help='Default AWS region to connect to')
    # Support for authentication using AWS access id and secret access key
    parser.add_argument(
        '-i',
        '--aws-id',
        default=None,
        help='AWS access key id to use')
    parser.add_argument(
        '-k',
        '--aws-secret-key',
        default=None,
        help='AWS secret access key to use')
    # Support for authentication using environmental variables
    parser.add_argument(
        '-e',
        '--env',
        action='store_true',
        default=False,
        help='Enable authentication using AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY via environmental vars')
    # verbosity switch, by default set to off
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        default=False,
        help='Display verbose output')
    # AWS resource parameter input via file, by default set to None
    parser.add_argument(
        '-f',
        '--file',
        default=None,
        help='Read AWS Resource parameters via text file')

    arguments = parser.parse_args()

    # if login from environmental variables was specified
    #if arguments.env:
    #    aws_id = os.getenv('AWS_ACCESS_KEY_ID', None)
    #    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY', None)
    #else:
    #    aws_id = arguments.aws_id
    #    aws_secret_key = arguments.aws_secret_key

    # adding mutual inclusivity for awd-id and secret-key-key
    #if aws_id and not aws_secret_key:
    #    parser.error('aws-id requires aws-secret-key')
    #elif not aws_id and aws_secret_key:
    #    parser.error('aws-secret-key requires aws-id')

    # build credentials dict
    credentials = {
        'profile': arguments.profile,
        'aws_access_key_id': aws_id,
        'aws_secret_access_key': aws_secret_key
    }

    # build params dictionary
    params = {
        'file': arguments.file,
        'region': arguments.region
    }

    verbose_mode = arguments.verbose

    return credentials, params, verbose_mode

