#!/usr/bin/env python3

import json
import logging
import os

import web

from waaas import perform

logging.basicConfig(
  filename='waaas.log', filemode='w', level=logging.DEBUG,
  format='%(asctime)s - %(levelname)s - %(message)s')

urls = ('/', 'index')

logging.info('starting up')


class index:
  def POST(self):
    logging.info("somebody is taking advantage of me")
    x = web.input(replay={})
    try:
      with open('game.WAgame', 'w+b') as f:
        f.write(x['replay'].file.read())
      os.system('./perform')
      web.header('Content-Type', 'application/json')
    except:
      raise web.badrequest('supply multipart form data with file in replay= format')
    try:
      return json.dumps(perform())
    except:
      raise web.internalerror("error while processing the replay file")
  
  def GET(self):
    return """
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <link rel="shortcut icon" href="https://zemke.io/images/icons/favicon.ico" type="image/x-icon" />
    <title>WAaaS</title>
    </head>
    <body>
      <h1>WAaaS</h1>
      <h2>Worms Armageddon as a Service</h2>
      <pre>curl -X POST 'https://waaas.zemke.io' -F 'replay=@game.WAgame'</pre>
      <br/>
      <a target="_blank" href="https://github.com/zemke/waaas">GitHub</a>
      &bull;
      <a target="_blank" href="https://hub.docker.com/r/zemke/docker-wa">Docker Hub</a>
    </body>
    </html>
    """


if __name__ == "__main__":
  app = web.application(urls, globals())
  app.run()
