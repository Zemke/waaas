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
  res["textureLength"] = int.from_bytes(f.read(1),byteorder='big')
  res["texture"] = struct.unpack(str(res["textureLength"]) + 's', f.read(res["textureLength"]))[0].decode()
  return res

if __name__ == '__main__':
  with open(sys.argv[1], "rb") as f:
    res = perform(f)
    if len(sys.argv) > 1:
      dest = sys.argv[2]
      if dest.lower().endswith(".png"):
        p = dest
      else:
        from random import choice
        from string import ascii_letters, digits
        from os import path
        p = path.join(dest, ''.join(choice(ascii_letters + digits) for _ in range(8))) + ".png"
      bbb.toimage(res["foreground"]).save(p, format='PNG')
    else:
      bbb.toimage(res["foreground"]).show()

      monochrome = bbb.toimage(res["monochrome"])
      bbb.mirror(monochrome).show()

      background = bbb.toimage(res["background"])
      bbb.mirror(background).show()

