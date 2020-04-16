#!/usr/bin/env python3

import struct
import sys

import bbb


def perform(f):
  """
  res["signature"] = f.read(4)
  res["length"] = struct.unpack('i', f.read(4))
  res["width"] = struct.unpack('i', f.read(4))
  res["height"] = struct.unpack('i', f.read(4))
  res["cavernBorder"] = struct.unpack('????', f.read(4))
  res["waterHeight"] = struct.unpack('i', f.read(4))
  # starting here things seem to go off from https://worms2d.info/Land_Data_file
  res["unknown"] = struct.unpack('i', f.read(4))
  res["structuresX"] = struct.unpack('i', f.read(4))
  res["structuresY"] = struct.unpack('i', f.read(4))
  """
  f.read(288)  # apparently 288 bytes till the img data
  return {"foreground": bbb.perform(f)}

if __name__ == '__main__':
  with open(sys.argv[1], "rb") as f:
    res = perform(f)
    bbb.toimage(res["foreground"]).show()

