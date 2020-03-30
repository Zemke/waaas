import pprint
import re
from typing import Dict, Optional, Any

res: Dict[str, Any] = {"messages": [], "turns": [], "suddenDeath": None}
timestamp_regex = "(?:\d\d:){2}\d\d\.\d\d"
timestamp_regex_w_brackets = "^\[%s\]" % timestamp_regex
action_prefix = " "  # some weird ISO-8859-1 encoded chars

turn: Dict[str, Optional[Dict]] = {"curr": None}


def create_damage(action):
  # Damage dealt: 28 (1 kill) to mloda kadra (Siwy), 64 to Men of faith (NNN`Rafka)
  # ['159 to mloda kadra (Siwy)', '100 (1 kill) to Men of faith (NNN`Rafka)']
  search = re.compile('^(\d+)(?: \((\d+) kills?\))? to .* \((.+)\)$').search(action)
  return {
    "damage": int(search.group(1)),
    "kills": int(search.group(2) or 0),
    "victim": search.group(3)
  }


def handle_action(line):
  action_search = \
    re.compile(f"\[({timestamp_regex})\] {action_prefix}(.*)$").search(line)
  if action_search:
    if "starts turn" in line:
      turn["curr"] = {
        "timestamp": action_search.group(1),
        "user": re.compile("\((.+\))").search(action_search.group(2)).group(1),
        "weapons": [],
        "damages": [],
      }
    elif "ends turn" in line or "loses turn due to loss of control" in line:
      ends_turn_search = re\
        .compile("; time used: ([\d.]+) sec turn, ([\d.]+) sec retreat$") \
        .search(action_search.group(2))
      turn["curr"]["timeUsedSeconds"] = float(ends_turn_search.group(1))
      turn["curr"]["retreatSeconds"] = float(ends_turn_search.group(2))
      turn["curr"]["lossOfControl"] = "loses turn due to loss of control" in line
      res["turns"].append(turn["curr"])
      turn["curr"] = None
    elif "fires" in line or "uses" in line:
      turn["curr"]["weapons"]\
        .append(re.compile("es (.*)$").search(action_search.group(2)).group(1))
    elif action_search.group(2).startswith("Damage dealt"):
      res["turns"][-1:][0]["damages"] = \
        list(map(create_damage, action_search.group(2)[14:].split(', ')))
    elif action_search.group(2) == "Sudden Death":
      res["suddenDeath"] = action_search.group(1)
    # todo could be something else when the it's not the last round
    elif action_search.group(2) == "Game Ends - Round Finished":
      res["gameEnd"] = action_search.group(1)
    else:
      pass
      # print("unprocessed", line)
      # current unprocessed are/
      # unprocessed [00:13:23.56]  Men of faith (NNN`Rafka) used 30 (12) units of Jet Pack fuel
      # unprocessed [00:15:13.24]  mloda kadra (Siwy) used 30 units of Jet Pack fuel
      # unprocessed [00:20:03.32]  resetting Jet Pack fuel use to 0
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
    else:
      # l is not '\n' and print("Unprocessed", l)
      # current unprocessed are
      # Unprocessed Red:       "Siwy"      as "mloda kadra"
      # Unprocessed Blue:      "NNN`Rafka" as "Men of faith" [Local Player]
      # Unprocessed Spectator: "SiD`" [Host]
      # Unprocessed Spectator: "TVPenguin"
      # Unprocessed Spectator: "TheExtremist"
      # Unprocessed Spectator: "waldek"
      # Unprocessed Team time totals:
      # Unprocessed mloda kadra (Siwy):       Turn: 00:09:02.62, Retreat: 00:00:59.70, Total: 00:10:02.32, Turn count: 25
      # Unprocessed Men of faith (NNN`Rafka): Turn: 00:14:04.06, Retreat: 00:01:16.04, Total: 00:15:20.10, Turn count: 26
      # Unprocessed End of round 3
      # Unprocessed Round time: 0:34:37
      # Unprocessed Total game time elapsed: 0:34:37
      # Unprocessed Men of faith wins the round.
      # Unprocessed Worm of the round: Michal (mloda kadra)
      # Unprocessed Most damage with one shot: 259 - Adam (Men of faith)

pprint.pprint(res)
