#!/usr/bin/env python3

import json
import re
import sys
from typing import Dict, Optional, Any

res: Dict[str, Any] = {}
timestamp_regex = "(?:\d\d:){2}\d\d\.\d\d"
timestamp_regex_w_brackets = "^\[%s\]" % timestamp_regex
action_prefix = " "  # some weird ISO-8859-1 encoded chars

turn: Dict[str, Optional[Dict]] = {"curr": None}
team_time_totals_line_appeared = {"curr": False}
team_regex = re.compile('(Red|Blue|Green|Yellow|Magenta|Cyan): +"(.+)" +as "(.+)"( \[Local Player\])?')
worm_placement = {"curr": None}


def init_res():
  res.clear()
  res["messages"] = []
  res["turns"] = []
  res["suddenDeath"] = None
  res["spectators"] = []
  res["teams"] = []
  res["teamTimeTotals"] = []
  res["wormPlacementCompleted"] = None
  res["wormPlacements"] = []


def create_damage(action):
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
        "user": re.compile(".+\((.+)\) starts turn$").search(action_search.group(2)).group(1),
        "weapons": [],
        "damages": [],
      }
    elif "is placing a Worm" in line:
      if worm_placement["curr"] is not None:
        res["wormPlacements"].append(worm_placement["curr"])
      worm_placement["curr"] = {
        "start": action_search.group(1),
        "user": re.compile(".+\((.+)\) is placing a Worm$").search(action_search.group(2)).group(1),
        "damages": []
      }
    elif 'Worm placement completed' in line:
      res["wormPlacements"].append(worm_placement["curr"])
      worm_placement["curr"] = None
      res["wormPlacementCompleted"] = \
          re.compile(f"\[({timestamp_regex})\] {action_prefix}(.*)$").search(line).group(1);
    elif "ends turn" in line or "loses turn due to loss of control" in line:
      ends_turn_search = re \
        .compile("; time used: ([\d.]+) sec turn, ([\d.]+) sec retreat$") \
        .search(action_search.group(2))
      turn["curr"]["timeUsedSeconds"] = float(ends_turn_search.group(1))
      turn["curr"]["retreatSeconds"] = float(ends_turn_search.group(2))
      turn["curr"]["lossOfControl"] = "loses turn due to loss of control" in line
      res["turns"].append(turn["curr"])
      turn["curr"] = None
    elif action_search.group(2).startswith("Damage dealt"):
      damages = []
      split = action_search.group(2)[14:].split('), ')
      for idx, dmg in enumerate(split):
        damages.append(create_damage(dmg + ")" if idx != len(split) - 1 else dmg))
      if len(res["turns"]) == 0:
        if worm_placement["curr"] is None:
          # Damage after "Worm placement completed" entry
          res["wormPlacements"][-1]["damages"] = damages
        else:
          worm_placement["curr"]["damages"] = damages
      else:
        res["turns"][-1:][0]["damages"] = damages
    elif "fires" in line or "uses" in line:
      if worm_placement["curr"] is not None and res["wormPlacementCompleted"] is None:
        worm_placement["curr"]["finish"] = action_search.group(1)
      else:
        turn["curr"]["weapons"] \
          .append(re.compile("\) (?:fires|uses) (.+?)(?: \(|$)").search(action_search.group(2)).group(1))
    elif action_search.group(2) == "Sudden Death":
      res["suddenDeath"] = action_search.group(1)
    elif action_search.group(2).startswith("Game Ends"):
      res["gameEnd"] = action_search.group(1)
    return
  message_search = re.compile(f"\[({timestamp_regex})\] \[(.+)\] (.+)$").search(line)
  if message_search:
    res["messages"].append({
      "timestamp": message_search.group(1),
      "user": message_search.group(2),
      "body": message_search.group(3)
    })
    return


def perform(lines):
  init_res()
  for l in lines:
    if re.search("({0}) ".format(timestamp_regex_w_brackets), l):
      handle_action(l)
    elif l.startswith("Game engine version: "):
      res["engineVersion"] = re.compile("Game engine version: (.+)").search(l).group(1)
    elif l.startswith("File Format Version: "):
      res["fileFormatVersion"] = re.compile("File Format Version: (.+)").search(l).group(1)
    elif l.startswith("Exported with Version: "):
      res["exportVersion"] = re.compile("Exported with Version: (.+)").search(l).group(1)
    elif l.startswith("Game ID: "):
      # Can be "extern" (might be related to RubberWorm) or quoted nummeric ID.
      res["gameId"] = re.compile("Game ID: \"(.+)\"").search(l).group(1)
    elif l.startswith("Game Started at "):
      res["startedAt"] = re.compile("Game Started at ([\d\- :]+ GMT)").search(l).group(1)
    elif l.startswith("Game Engine Version: "):
      res["engineVersion"] = re.compile("Game Engine Version: (.+)$").search(l).group(1)
    elif l.startswith("Exported with Version: "):
      res["exportVersion"] = re.compile("Exported with Version: (.+)$").search(l).group(1)
    elif l.startswith("File Format Version: "):
      file_format_groups = re.compile("File Format Version: (.+) - (.+)$").search(l)
      res["fileFormatVersion"] = [file_format_groups.group(1), file_format_groups.group(2)]
    elif l.startswith("Spectator"):
      spectator_search = re.compile("Spectator: \"(.+)\"( \[Host\])?").search(l)
      res["spectators"].append({
        "user": spectator_search.group(1),
        "host": spectator_search.group(2) is not None
      })
    elif l.startswith("Most damage with one shot"):
      # Worm name matching with asterisk rather than plus 'cause I've seen empty worm names.
      most_dmg_w_one_shot_search = re.compile("Most damage with one shot: (\d+) - (.*) \((.*)\)").search(l)
      res["mostDamageWithOneShot"] = {
        "damage": most_dmg_w_one_shot_search.group(1),
        "worm": most_dmg_w_one_shot_search.group(2),
        "team": most_dmg_w_one_shot_search.group(3),
      }
    elif l.startswith("Most kills with one shot"):
      # Worm name matching with asterisk rather than plus 'cause I've seen empty worm names.
      most_kills_w_one_shot_search = re.compile("Most kills with one shot: (\d+) - (.*) \((.*)\)").search(l)
      res["mostKillsWithOneShot"] = {
        "damage": most_kills_w_one_shot_search.group(1),
        "worm": most_kills_w_one_shot_search.group(2),
        "team": most_kills_w_one_shot_search.group(3),
      }
    elif " wins the round." in l:
      res["winsTheRound"] = re.compile("(.+) wins the round\.").search(l).group(1)
    elif " wins the match!" in l:
      res["winsTheMatch"] = re.compile("(.+) wins the match!").search(l).group(1)
    elif l.startswith("Worm of the round: "):
      # Worm name matching with asterisk rather than plus 'cause I've seen empty worm names.
      worm_of_the_round_search = re.compile("Worm of the round: (.*) \((.+)\)").search(l)
      res["wormOfTheRound"] = {
        "worm": worm_of_the_round_search.group(1),
        "team": worm_of_the_round_search.group(2),
      }
    elif l.startswith("Round time: "):
      res["roundTime"] = re.compile("Round time: (.+)").search(l).group(1)
    elif l.startswith("Total game time elapsed: "):
      res["totalGameTimeElapsed"] = re.compile("Total game time elapsed: (.+)").search(l).group(1)
    elif team_regex.search(l):
      team_search = team_regex.search(l)
      res["teams"].append({
        "color": team_search.group(1),
        "user": team_search.group(2),
        "team": team_search.group(3),
        "localPlayer": team_search.group(4) is not None
      })
    elif l.startswith("Team time totals:"):
      team_time_totals_line_appeared["curr"] = True
    elif (team_time_totals_line_appeared["curr"]
          and "Turn count" in l and "Total" in l and "Retreat" in l and "Turn" in l):
      team_time_totals_search = re \
        .compile(' *(.+) \((.+)\): +Turn: ([\d:.]+), Retreat: ([\d:.]+), Total: ([\d:.]+), Turn count: (\d+)$') \
        .search(l)
      res["teamTimeTotals"].append({
        "team": team_time_totals_search.group(1),
        "user": team_time_totals_search.group(2),
        "turn": team_time_totals_search.group(3),
        "retreat": team_time_totals_search.group(4),
        "total": team_time_totals_search.group(5),
        "turnCount": int(team_time_totals_search.group(6)),
      })
    elif 'The round was drawn.' in l:
      res["winsTheRound"] = None
  return res


if __name__ == '__main__':
  encoding="ISO-8859-1"
  errors="ignore"
  if len(sys.argv) < 2:
    sys.stdin.reconfigure(encoding=encoding, errors=errors)
    perform(sys.stdin.read().splitlines())
  else:
    with open(sys.argv[1], encoding=encoding, errors=errors) as arg_f:
      perform(arg_f.readlines())
  print(json.dumps(res, indent=4))

