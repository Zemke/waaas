#!/usr/bin/env python3

import struct
import sys

import bbb


def perform(f):
  res = {}
  res["signature"] = f.read(4)
  res["length"] = struct.unpack('i', f.read(4))
  res["width"] = struct.unpack('i', f.read(4))
  res["height"] = struct.unpack('i', f.read(4))
  res["cavernBorder"] = struct.unpack('????', f.read(4))
  res["waterHeight"] = struct.unpack('i', f.read(4))
  res["unknown"] = struct.unpack('i', f.read(4))
  res["numOfStructures"] = struct.unpack('i', f.read(4))
  f.read(res["numOfStructures"][0] * 2 * 4)
  res["foreground"] = bbb.perform(f)
  res["monochrome"] = bbb.perform(f)
  res["background"] = bbb.perform(f)
  return res

if __name__ == '__main__':
  with open(sys.argv[1], "rb") as f:
    res = perform(f)
    bbb.toimage(res["foreground"]).show()

    monochrome = bbb.toimage(res["monochrome"])
    bbb.mirror(monochrome).show()

    background = bbb.toimage(res["background"])
    bbb.mirror(background).show()

