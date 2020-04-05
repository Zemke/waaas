#!/usr/bin/env python3

import pprint
import re
from typing import Dict, Optional, Any

res: Dict[str, Any] = {"messages": [], "turns": [], "suddenDeath": None,
                       "spectators": [], "teams": [], "teamTimeTotals": []}
timestamp_regex = "(?:\d\d:){2}\d\d\.\d\d"
timestamp_regex_w_brackets = "^\[%s\]" % timestamp_regex
action_prefix = " "  # some weird ISO-8859-1 encoded chars

turn: Dict[str, Optional[Dict]] = {"curr": None}
team_time_totals_line_appeared = {"curr": False}
team_regex = re.compile('(Red|Blue|Green|Yellow|Magenta|Cyan): +"(.+)" +as "(.+)"( \[Local Player\])?')


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
    elif "ends turn" in line or "loses turn due to loss of control" in line:
      ends_turn_search = re \
        .compile("; time used: ([\d.]+) sec turn, ([\d.]+) sec retreat$") \
        .search(action_search.group(2))
      turn["curr"]["timeUsedSeconds"] = float(ends_turn_search.group(1))
      turn["curr"]["retreatSeconds"] = float(ends_turn_search.group(2))
      turn["curr"]["lossOfControl"] = "loses turn due to loss of control" in line
      res["turns"].append(turn["curr"])
      turn["curr"] = None
    elif "fires" in line or "uses" in line:
      turn["curr"]["weapons"] \
        .append(re.compile("es (.+?)(?: \(|$)").search(action_search.group(2)).group(1))
    elif action_search.group(2).startswith("Damage dealt"):
      res["turns"][-1:][0]["damages"] = \
        list(map(create_damage, action_search.group(2)[14:].split(', ')))
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


def perform():
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
      elif l.startswith("Spectator"):
        spectator_search = re.compile("Spectator: \"(.+)\"( \[Host\])?").search(l)
        res["spectators"].append({
          "user": spectator_search.group(1),
          "host": spectator_search.group(2) is not None
        })
      elif l.startswith("Most damage with one shot"):
        most_dmg_w_one_shot_search = re.compile("Most damage with one shot: (\d+) - (.+) \((.*)\)").search(l)
        res["mostDamageWithOneShot"] = {
          "damage": most_dmg_w_one_shot_search.group(1),
          "worm": most_dmg_w_one_shot_search.group(2),
          "team": most_dmg_w_one_shot_search.group(3),
        }
      elif " wins the round." in l:
        res["winsTheRound"] = re.compile("(.+) wins the round\.").search(l).group(1)
      elif l.startswith("Worm of the round: "):
        worm_of_the_round_search = re.compile("Worm of the round: (.+) \((.+)\)").search(l)
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
  return res


if __name__ == '__main__':
  perform()
  pprint.pprint(res)
