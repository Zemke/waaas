#!/usr/bin/env python3

import sys
import boto3

import re
import json
import os
import time
from tempfile import NamedTemporaryFile, TemporaryDirectory, gettempdir

import waaas
import land
import bbb


# {
#   "Records": [
#     {
#       "eventVersion": "2.1",
#       "eventSource": "aws:s3",
#       "awsRegion": "us-east-2",
#       "eventTime": "2019-09-03T19:37:27.192Z",
#       "eventName": "ObjectCreated:Put",
#       "userIdentity": {
#         "principalId": "AWS:AIDAINPONIXQXHT3IKHL2"
#       },
#       "requestParameters": {
#         "sourceIPAddress": "205.255.255.255"
#       },
#       "responseElements": {
#         "x-amz-request-id": "D82B88E5F771F645",
#         "x-amz-id-2": "vlR7PnpV2Ce81l0PRw6jlUpck7Jo5ZsQjryTjKlc5aLWGVHPZLj5NeC6qMa0emYBDXOo6QBU0Wo="
#       },
#       "s3": {
#         "s3SchemaVersion": "1.0",
#         "configurationId": "828aa6fc-f7b5-4305-8584-487c791949c1",
#         "bucket": {
#           "name": "lambda-artifacts-deafc19498e3f2df",
#           "ownerIdentity": {
#             "principalId": "A3I5XTEXAMAI3E"
#           },
#           "arn": "arn:aws:s3:::lambda-artifacts-deafc19498e3f2df"
#         },
#         "object": {
#           "key": "b21b84d653bb07b05b1e6b33684dc11b",
#           "size": 1305107,
#           "eTag": "b21b84d653bb07b05b1e6b33684dc11b",
#           "sequencer": "0C0F6F405D6ED209E1"
#         }
#       }
#     }
#   ]
# }


# TODO In WAaaS main repo split the logic from the web code so the logic can be reused here.


def handler(event, context):
  print("Received event: ", event)
  print("Context: ", context)
  s3 = boto3.resource('s3')
  obj = s3.Object('waaas-input', event['Records'][0]["s3"]["object"]["key"])
  with NamedTemporaryFile(mode='wb', prefix='waaas_', suffix="_replay") as replay_file:
    obj.download_fileobj(replay_file)
    handle(replay_file)


def handle(replay_file):
  with NamedTemporaryFile(mode='r+', prefix='waaas_', suffix="_log", encoding="ISO-8859-1") as log_file:
    mapjson = None
    texturejson = None
    with TemporaryDirectory(prefix="waaas_", suffix="_land") as land_dir:
      os.system('wa-getlog < {} > {}'.format(replay_file.name, log_file.name))
      with open('/root/.wine/drive_c/WA/DATA/land.dat', mode='rb') as land_file:
        with NamedTemporaryFile(mode='wb', prefix='waaas_', suffix="_map", delete=False) as map_file:
          landres = land.perform(land_file)
          bbb.toimage(landres["foreground"]).save(map_file, format='PNG')
          texturejson = landres["texture"]
          mapjson = "/map/" + re.compile("/waaas_(.+)_map").search(map_file.name).group(1)
    if os.stat(log_file.name).st_size == 0:
      raise Exception("could not process replay file")
    logjson = waaas.perform(log_file)
    logjson["map"] = mapjson
    logjson["texture"] = texturejson
    result = json.dumps(logjson)
    print("result:\n", result)
    return result
    # TODO upload map file to S3 waaas-output
    # TODO send JSON to SQS


if __name__ == "__main__":
  f = sys.argv[1]
  print("running from cli for file", f)
  with open(f, 'rb') as replay_file:
    handle(replay_file)

