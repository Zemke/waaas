import pprint
import re

res = {"messages": []}
timestamp_regex = "(?:\d\d:){2}\d\d\.\d\d"
timestamp_regex_w_brackets = "^\[%s\]" % timestamp_regex
action_prefix = " "  # some weird ISO-8859-1 encoded chars


def handle_action(line):
  if re.compile(f"{timestamp_regex_w_brackets} {action_prefix}").search(line):
    print('action', line)
    return
  
  message_search = re.compile(f"\[({timestamp_regex})\] \[(.+)\] (.+)$").search(line)
  if message_search:
    print('message', line)
    res["messages"].append({
      "timestamp": message_search.group(1),
      "user": message_search.group(2),
      "body": message_search.group(3)
    })
    return


with open("game.log", encoding="ISO-8859-1", errors='ignore') as f:
  for l in f.readlines():
    if re.search("({0}) ".format(timestamp_regex_w_brackets), l):
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

pprint.pprint(res)
