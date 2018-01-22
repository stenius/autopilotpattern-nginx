#!/usr/bin/env python
import boto3
import consul
import os


AWS_DOMAIN = os.environ.get('AWS_DOMAIN', None)
DNS_DOMAIN = os.environ.get('DNS_DOMAIN', None)
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', None)
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', None)

if AWS_DOMAIN:
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        print('ERROR: Missing AWS Access Key ID or Secret')
    consul_client = consul.Consul()
    route53_client = boto3.client('route53',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    zone_name = AWS_DOMAIN + '.'

    aws_zone_id = [zone for zone in route53_client.list_hosted_zones()['HostedZones'] if zone['Name'] == zone_name][0]['Id'].split('/')[-1]

    index, nodes = consul_client.catalog.service('nginx-public')
    nodes = list(set([node['ServiceAddress'] for node in nodes]))

    response = route53_client.change_resource_record_sets(
        HostedZoneId=aws_zone_id,
        ChangeBatch={
            'Changes': [
                {
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': DNS_DOMAIN,
                        'Type': 'A',
                        'TTL': 300,
                        'ResourceRecords': [{'Value': node} for node in nodes],
                    }
                },
            ]
        }
    )
    print('DNS Updated')
