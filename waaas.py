import re

res = {}
timestamp_regex = "^\[(?:\d\d:){2}\d\d\.\d\d\] "
action_prefix = " "  # some weird ISO-8859-1 encoded strings


def handle_action(line):
  if re.compile(timestamp_regex + action_prefix).search(line):
    print('action', line)
  else:
    print('message', line)


with open("game.log", encoding="ISO-8859-1", errors='ignore') as f:
  for l in f.readlines():
    if re.search(timestamp_regex, l):
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
