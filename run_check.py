#!/usr/bin/env python

import os
import datetime as dt

import boto3
from dotenv import load_dotenv
from check_tls_certs import get_domain_certs, check_domains, domain_definitions_from_filename

load_dotenv()

EXPIRY_DATE_WARN_PERIOD_DAYS = 14


def get_object_from_s3(bucket_name, file_name):
    s3 = boto3.resource('s3')
    s3.Bucket(bucket_name).download_file(file_name, file_name)


def is_amazon_cert(status_list):
    return any(level == 'info' and 'Amazon' in text for level, text in status_list)


if __name__ == '__main__':

    get_object_from_s3(os.environ['S3_BUCKET'], os.environ['FILE_NAME'])
    domains = domain_definitions_from_filename(os.environ['FILE_NAME'])

    domain_certs = get_domain_certs(domains)
    results = check_domains(domains, domain_certs, dt.datetime.utcnow())

    for domain_list, status_list, expiry_date in results:
        if is_amazon_cert(status_list):
            print('Certificate for domain(s) {} belongs to Amazon. Skipping'.format(
                ' / '.join(domain_list)))

            continue

        print('Cert for domains: {}\n status:\n {}\n'.format(
            ' / '.join(domain_list),
            '\n'.join([level + ': ' + text for level, text in status_list])))

