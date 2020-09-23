#!/usr/bin/env python3
import logging
import boto3
from botocore.exceptions import NoCredentialsError
import socket
import os
from requests import get
from time import sleep

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
r53 = boto3.client('route53')

# ======================================================= CONFIG/ENV
hosted_zone_id = os.environ["HOSTED_ZONE_ID"]
target_record_name = os.environ["TARGET_RECORD_NAME"]  # your.site.com.

try:
    ttl = int(os.environ["TTL"])
except KeyError:
    ttl = 300  # Default

try:
    interval_mins = int(os.environ["INTERVAL_MINS"])
except KeyError:
    interval_mins = 20  # Default
# =======================================================


def upsert_record(target_record, ip):
    """Upsert the given A record with the given IP"""
    try:
        response = r53.change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            ChangeBatch={'Comment': 'Upserting A Record',
                         'Changes': [
                             {
                                 'Action': 'UPSERT',
                                 'ResourceRecordSet': {
                                     'Name': target_record,
                                     'Type': 'A',
                                     'TTL': ttl,
                                     'ResourceRecords': [
                                         {
                                             'Value': ip
                                         },
                                     ],
                                 }
                             },
                         ]
                         }
        )
        logger.debug(response)
        logger.info(f"Record updated")
    except NoCredentialsError:
        raise RuntimeError("Problem locating AWS credentials.\n"
                           "Make sure your credentials file exists on the host: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html\n"
                           "Make sure you map the aws credentials folder as a volume in your run command: -v $HOME/.aws:/root/.aws")


if __name__ == "__main__":
    while True:
        # Get our current public IP
        actual_ip = get('https://api.ipify.org').text

        # Attempt to resolve the target record
        try:
            dns_ip = socket.gethostbyname(target_record_name[:-1])
        except socket.gaierror as e:
            logger.error(e)
            logger.warning(f"Unable to resolve the target DNS record, it may not exist yet. {target_record_name=}")
            dns_ip = None

        # If they're different, update the target record
        logger.debug(f"{dns_ip=} {actual_ip=}")
        if dns_ip != actual_ip:
            logger.info(f"New IP detected: {actual_ip}  Updating route53...")
            upsert_record(target_record_name, actual_ip)
        else:
            logger.info(f"{actual_ip} is current. Sleeping for {interval_mins}m")

        sleep(60 * interval_mins)
