#!/usr/bin/env python3

import struct
import sys
from PIL import Image

res = {}

with open(sys.argv[1], "rb") as f:
  res["signature"] = struct.unpack('i', f.read(4))
  res["length"] = struct.unpack('i', f.read(4))
  res["bpp"] = struct.unpack('b', f.read(1))
  res["flags"] = f.read(1)
  res["numOfColors"] = struct.unpack('h', f.read(2))
  res["palette"] = [0,0,0]
  for c in range(int(res["numOfColors"][0])):
    res["palette"].append(struct.unpack('B', f.read(1))[0])
    res["palette"].append(struct.unpack('B', f.read(1))[0])
    res["palette"].append(struct.unpack('B', f.read(1))[0])
  res["width"] = struct.unpack('h', f.read(2))
  res["height"] = struct.unpack('h', f.read(2))
  res["data"] = f.read()

img = Image.frombytes('P', (res["width"][0], res["height"][0]), res["data"])
img.putpalette(res["palette"])
img.show()

