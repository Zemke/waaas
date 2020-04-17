#!/usr/bin/env python3

import struct
import sys
from PIL import Image, ImageOps
from sys import exit


def perform(f):
  res = {}
  res["signature"] = struct.unpack('i', f.read(4))
  res["length"] = struct.unpack('i', f.read(4))
  res["bpp"] = struct.unpack('b', f.read(1))
  res["flags"] = f.read(1)
  if res["flags"] == b'\x80':
    res["numOfColors"] = struct.unpack('h', f.read(2))
    res["palette"] = [0,0,0]
    for c in range(int(res["numOfColors"][0])):
      res["palette"].append(struct.unpack('B', f.read(1))[0])
      res["palette"].append(struct.unpack('B', f.read(1))[0])
      res["palette"].append(struct.unpack('B', f.read(1))[0])
  res["width"] = struct.unpack('h', f.read(2))
  res["height"] = struct.unpack('h', f.read(2))

  datalength = int(res["width"][0] * res["height"][0] * res["bpp"][0] / 8)
  if res["bpp"][0] == 1:
    res["data"] = b''
    for _ in range(int(datalength/240)):
      b = f.read(240)
      res["data"] += b[::-1]
  else:
    res["data"] = f.read(datalength)

  return res


def swapbits(b, odd):
  res1 = bin(b[0])[2:][::-1].zfill(8)
  if odd:
    res1 = sorted(list(map(lambda x: int(x), [char for char in res1])), reverse=True)
  else:
    res1 = sorted(list(map(lambda x: int(x), [char for char in res1])), reverse=False)
  res1 = ''.join(map(lambda x: str(x), res1))
  res2 = hex(int(res1,2))
  res3 = bytes.fromhex(res2[2:].zfill(2))
  return res3


def toimage(res):
  mode = "P" if "palette" in res else "1"
  img = Image.frombytes(mode, (res["width"][0], res["height"][0]), res["data"])
  if "palette" in res:
    img.putpalette(res["palette"])
  return img


def mirror(img):
  return ImageOps.mirror(img)


if __name__ == '__main__':
  with open(sys.argv[1], "rb") as f:
    res = perform(f)
    toimage(res).show()

