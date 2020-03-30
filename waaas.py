import re

res = {}

with open("game.log", encoding="utf8", errors='ignore') as f:
  for line in f.readlines():
    if line.startswith("Game ID: "):

      print(line)
      res["gameId"] = re.compile("Game ID: \"(\d+)\"").search(line).group(1)


      
print(res)

