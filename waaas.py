print("It's going wild")

with open("game.log", encoding="utf8", errors='ignore') as f:
  for line in f.readlines():
    print(line)

