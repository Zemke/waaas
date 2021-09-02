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
    os.system('wa-getlog < {} > {}'.format(replay_file.name, log_file.name))
    with open('/mnt/wine/.wine/drive_c/WA/DATA/land.dat', mode='rb') as land_file:
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

