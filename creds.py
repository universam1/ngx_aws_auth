import boto3
import base64
import hashlib
import hmac
import subprocess

from datetime import datetime
from pprint import pprint
from botocore.credentials import InstanceMetadataProvider, InstanceMetadataFetcher
from subprocess import call


filename = '/etc/nginx/awssecrets.conf'
service = 's3'
now = datetime.utcnow().date()
ymd = '%04d%02d%02d' % (now.year, now.month, now.day)

def sign(key, val):
    return hmac.new(key, val.encode('utf-8'), hashlib.sha256).digest()

def getSignatureKey(key, dateStamp, regionName, serviceName):
    kDate = sign(("AWS4" + key).encode("utf-8"), dateStamp)
    kRegion = sign(kDate, regionName)
    kService = sign(kRegion, serviceName)
    kSigning = sign(kService, "aws4_request")
    return kSigning

provider = InstanceMetadataProvider(iam_role_fetcher=InstanceMetadataFetcher(timeout=1000, num_attempts=2))
creds = provider.load()
pprint(vars(creds))

access_key = creds.access_key
secret_key = creds.secret_key
my_session = boto3.session.Session()
region = my_session.region_name
signature = getSignatureKey(secret_key, ymd, region, service)
signature = base64.b64encode(signature).decode('ascii')

# print('aws_access_key: %s' % access_key)
print('secret_key: %s' %  secret_key)
# print('aws_signing_key: %s' % signature)
# print('aws_key_scope: %s/%s/%s/aws4_request' % (ymd, region, service))

f = open(filename, 'w')
f.write('aws_access_key %s;\n' % access_key)
f.write('aws_signing_key %s;\n' % signature)
f.write('aws_key_scope %s/%s/%s/aws4_request;\n' % (ymd, region, service))
f.close()

with open(filename, 'r') as fin:
    print fin.read()

print 'reload nginx SIGHUP'

command = ['/usr/sbin/service', "nginx", 'reload'];
#shell=FALSE for sudo to work.
subprocess.call(command, shell=False)
