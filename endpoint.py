import json
import os

import web

from waaas import perform

urls = (
  '/', 'index'
)


class index:
  def POST(self):
    x = web.input(replay={})
    with open('game.WAgame', 'w+b') as f:
      f.write(x['replay'].file.read())
    os.system('./perform')
    web.header('Content-Type', 'application/json')
    return json.dumps(perform())


if __name__ == "__main__":
  app = web.application(urls, globals())
  app.run()
