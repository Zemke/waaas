#!/usr/bin/env python3

import struct
import sys

import bbb

res = {}

with open(sys.argv[1], "rb") as f:
  print(f.read(288))  # Apparently 288 bytes till the img data
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
  res["foreground"] = bbb.perform(f)
  #print("foreground", res["foreground"])
  bbb.toimage(res["foreground"]).show()

#print(res)


