import re

res = {}

with open("game.log", encoding="utf8", errors='ignore') as f:
  for line in f.readlines():
    if line.startswith("Game ID: "):
      res["gameId"] = re.compile("Game ID: \"(\d+)\"").search(line).group(1)
      continue
    if line.startswith("Game Started at "):
      res["startedAt"] = re.compile("Game Started at ([\d\- :]+ GMT)").search(line).group(1)
      continue


      
print(res)

