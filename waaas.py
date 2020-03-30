import re

res = {}


def handle_action(line):
  pass


with open("game.log", encoding="utf8", errors='ignore') as f:
  for l in f.readlines():
    if re.search("^\[(?:\d\d:){2}\d\d\.\d\d\] ", l):
      handle_action(l)
    elif l.startswith("Game ID: "):
      res["gameId"] = re.compile("Game ID: \"(\d+)\"").search(l).group(1)
    elif l.startswith("Game Started at "):
      res["startedAt"] = re.compile("Game Started at ([\d\- :]+ GMT)").search(l).group(1)
    elif l.startswith("Game Engine Version: "):
      res["engineVersion"] = re.compile("Game Engine Version: (.+)$").search(l).group(1)
    elif l.startswith("Exported with Version: "):
      res["exportVersion"] = re.compile("Exported with Version: (.+)$").search(l).group(1)
    elif l.startswith("File Format Version: "):
      file_format_groups = re.compile("File Format Version: (.+) - (.+)$").search(l)
      res["fileFormatVersion"] = [file_format_groups.group(1), file_format_groups.group(2)]

print(res)
