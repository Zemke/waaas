import json
import os

import web

from waaas import perform

urls = (
  '/', 'index'
)


class index:
  def POST(self):
    os.system('./perform')
    web.header('Content-Type', 'application/json')
    return json.dumps(perform())


if __name__ == "__main__":
  app = web.application(urls, globals())
  app.run()
