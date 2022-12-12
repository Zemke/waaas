#!/usr/bin/env python3

import re
import json
import logging
import os
import time
from tempfile import NamedTemporaryFile, TemporaryDirectory, gettempdir

import web

import waaas
import land
import bbb

logging.basicConfig(
  filename='waaas.log', filemode='w', level=logging.DEBUG,
  format='%(asctime)s - %(levelname)s - %(message)s')

urls = (
  '/', 'index',
  '/map/([^/]+)/?', 'map',
  '/log/([^/]+)/?', 'log',
)

logging.info('starting up')


class map:
  def GET(self, name):
    return open(gettempdir() + "/waaas_{0}_map".format(name), 'rb').read()


class log:
  def GET(self, name):
    return open(gettempdir() + "/waaas_{0}_log".format(name), 'r', encoding="ISO-8859-1").read()


class index:
  def POST(self):
    logging.info("somebody is taking advantage of me")
    inp = web.input()
    if "replay" not in inp:
      raise web.badrequest('supply multipart form data with file in replay= format')
    while web.running:
      time.sleep(1)
    logging.info("done waiting")
    try:
      with NamedTemporaryFile(mode='wb', prefix='waaas_', suffix="_replay") as replay_file:
        replay_file.write(inp['replay'])
        with NamedTemporaryFile(mode='r+', prefix='waaas_', suffix="_log", encoding="ISO-8859-1", delete=False) as log_file:
          web.running = True
          mapjson = None
          logfilejson = None
          texturejson = None
          with TemporaryDirectory(prefix="waaas_", suffix="_land") as land_dir:
            os.system('./perform ' + land_dir + ' ' +  replay_file.name + ' ' + log_file.name)
            with open(land_dir + "/land.dat", mode='rb') as land_file:
              try:
                with NamedTemporaryFile(mode='wb', prefix='waaas_', suffix="_map", delete=False) as map_file:
                  landres = land.perform(land_file)
                  bbb.toimage(landres["foreground"]).save(map_file, format='PNG')
                  texturejson = landres["texture"]
                  mapjson = "/map/" + re.compile("/waaas_(.+)_map").search(map_file.name).group(1)
              except Exception as e:
                logging.exception(e)
          logfilejson = "/log/" + re.compile("/waaas_(.+)_log").search(log_file.name).group(1)
          web.header('Content-Type', 'application/json')
          if os.stat(log_file.name).st_size == 0:
            raise web.internalerror("could not process replay file")
          try:
            logjson = waaas.perform(log_file)
            logjson["map"] = mapjson
            logjson["log"] = logfilejson
            logjson["texture"] = texturejson
            return json.dumps(logjson)
          except Exception as e:
            logging.exception(e)
            raise web.internalerror("error while processing the replay file")
    finally:
      web.running = False
  
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
      <a target="_blank" href="https://github.com/zemke/wa-docker">Headless WA</a>
      &bull;
      <a target="_blank" href="https://worms2d.info/WAaaS">WKB</a>
      <br/>
      <hr/>
      <br/>
      <form action="/" method="POST" target="_blank" enctype="multipart/form-data">
        <label for="replay">Replay</label>
        <input type="file" id="replay" name="replay" accept="*.WAgame"/>
        <input type="submit" value="Submit" />
      </form>
    </body>
    </html>
    """


if __name__ == "__main__":
  web.running = False
  app = web.application(urls, globals())
  app.run()
