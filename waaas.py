import pprint
import re
from typing import Dict, Optional, Any

res: Dict[str, Any] = {"messages": [], "turns": []}
timestamp_regex = "(?:\d\d:){2}\d\d\.\d\d"
timestamp_regex_w_brackets = "^\[%s\]" % timestamp_regex
action_prefix = " "  # some weird ISO-8859-1 encoded chars

action = []
turn: Dict[str, Optional[Dict]] = {"curr": None}


def handle_action(line):
  action_search = re.compile(f"\[({timestamp_regex})\] {action_prefix}(.*)$").search(line)
  if action_search:
    action.append(action_search.group(2))  # todo debugging
    if "starts turn" in line:
      turn["curr"] = {
        "timestamp": action_search.group(1),
        "user": re.compile("\((.+\))").search(action_search.group(2)).group(1),
        "weapons": []
      }
    elif "ends turn" in line:
      ends_turn_search = re.compile("ends turn; time used: ([\d.]+) sec turn, ([\d.]+) sec retreat$") \
        .search(action_search.group(2))
      turn["curr"]["timeUsedSeconds"] = ends_turn_search.group(1)
      turn["curr"]["retreatSeconds"] = ends_turn_search.group(2)
      res["turns"].append(turn["curr"])  # todo could be by reference perhaps
      turn["curr"] = None
    elif "fires" in line or "uses" in line:
      turn["curr"]["weapons"].append(re.compile("es (.*)$").search(action_search.group(2)).group(1))
    return
  message_search = re.compile(f"\[({timestamp_regex})\] \[(.+)\] (.+)$").search(line)
  if message_search:
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

pprint.pprint(action)
pprint.pprint(res)
