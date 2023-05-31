#!/usr/bin/env python3

import re
import json
import logging
import os
import time
from subprocess import Popen


from tempfile import NamedTemporaryFile, TemporaryDirectory, gettempdir
import pickle
from pathlib import Path
import shutil

import web

import waaas
import land
import bbb

DIR = Path(__file__).parent.absolute()

# TODO just log to stdout
logging.basicConfig(
  filename='waaas.log', filemode='w', level=logging.DEBUG,
  format='%(asctime)s - %(levelname)s - %(message)s')

urls = (
  '/', 'index',
  '/map/([^/]+)/?', 'map',
  '/log/([^/]+)/?', 'log',
  '/getvideo/?([^/]+)?/?([^/]+)?/?', 'getvideo',
)

logging.info('starting up')


def pid_running(pid):
  try:
    os.kill(pid, 0)
  except OSError:
    return False
  else:
    return True


class map:
  def GET(self, name):
    return open(gettempdir() + "/waaas_{0}_map".format(name), 'rb').read()


class log:
  def GET(self, name):
    return open(gettempdir() + "/waaas_{0}_log".format(name), 'r', encoding="ISO-8859-1").read()


class getvideo:
  def GET(self, name, action):
    if name is None or action is None:
      raise web.notfound()
    dest = os.path.join(gettempdir(), f"waaas_{name}_getvideo")
    persist_f = os.path.join(DIR, 'persist', name + '.pickle')
    if not os.path.exists(persist_f):
      raise Exception('could not find persisted process ' + persist_f)
    with open(persist_f, 'rb') as f:
      persist = pickle.load(f)
    if not os.path.exists(dest):
      raise web.notfound('no such process')
    if action == "status":
      cnt = 0
      for n in os.listdir(dest):
        f = os.path.join(dest, n)
        if os.path.isfile(f) and os.path.splitext(f)[-1].lower() == ".png":
          cnt += 1
      web.header('Content-Type', 'application/json')
      return json.dumps(dict(
        done=(done := pid_running(persist["pid"])),
        ready=cnt,
        expected=(expected := persist["expected"]),
        progress=1. if done else round(cnt / persist["expected"], 2),
        remaining=0 if done else (remaining := (expected - cnt)),
        estimate_s=0 if done else round(cnt / (time.time() - persist["now"]) * remaining),
        zero_indexed=True,
      ))
    elif action.isdigit():
      f = os.path.join(
        gettempdir(),
        f"waaas_{name}_getvideo",
        f"video_{action.rjust(6, '0')}.png")
      if not os.path.exists(f):
        raise web.notfound(f"file at position {action} does not exist")
      web.header('Content-Type', 'image/x-png')
      return open(f, 'rb').read()
    elif action == "ack":
      interrupt = pid_running(persist["pid"])
      if interrupt:
        os.kill(persist["pid"], 15)
      logging.info("log from docker:")
      #with open(log_f := os.path.join(DIR, 'persist', name + '.log'), 'r') as f:
      #  logging.info(f.read())
      web.header('Content-Type', 'application/json')
      #os.remove(log_f)
      print(dest)
      shutil.rmtree(dest)
      os.remove(persist_f)
      return json.dumps(dict(interrupted=interrupt))
    else:
      raise web.notfound("no action for " + action)

  def POST(self, name, action):
    # TODO check x-getvideo token
    # TODO check previous getvideo chunk has been acknowledged and disk space freed

    logging.info("somebody is taking advantage of me")
    inp = web.input()
    if "replay" not in inp:
      raise web.badrequest('supply multipart form data with file in replay= format')
    logging.info("done waiting")
    replay_file = NamedTemporaryFile(mode='wb', prefix='waaas_', suffix="_replay", delete=False)
    replay_file.write(inp['replay'])

    # validate fps
    fps = 20
    if 'fps' in inp:
      if not inp['fps'].isdigit() or int(inp['fps']) < 1 or int(inp['fps']) > 30:
        raise web.badrequest('fps must be an integer from 1 to 30')
      fps = int(inp['fps'])

    # validate x
    x = 640
    if 'x' in inp:
      if 'y' not in inp:
        raise web.badrequest('x is provided but y is missing')
      if not inp['x'].isdigit() or int(inp['x']) < 640 or int(inp['x']) > 1920:
        raise web.badrequest('x must be an integer from 640 to 1920')
      x = int(inp['x'])

    # validate y
    y = 480
    if 'y' in inp:
      if 'x' not in inp:
        raise web.badrequest('y is provided but x is missing')
      if not inp['y'].isdigit() or int(inp['y']) < 640 or int(inp['y']) > 1080:
        raise web.badrequest('y must be an integer from 480 to 1080')
      y = int(inp['y'])

    # validate start
    start = 0
    if 'start' in inp:
      if not inp['start'].isdigit() or int(inp['start']) < 0 or int(inp['start']) > 3600:
        raise web.badrequest('start must be an integer from 0 to 3600')
      start = int(inp['start'])

    # validate end
    end = 50
    if 'end' in inp:
      if not inp['end'].isdigit() or int(inp['end']) < 1 or int(inp['end']) > 3600:
        raise web.badrequest('end must be an integer from 1 to 3600')
      end = int(inp['end'])

    dur = end - start
    if dur > 50:
      raise web.badrequest('exported gameplay must not be longer than 50 soconds')

    params = dict(fps=fps, start=start, end=end, x=x, y=y)
    tmpdir_opts = dict(prefix="waaas_", suffix="_getvideo")
    getvideo_dir = TemporaryDirectory(**tmpdir_opts)
    name = os.path.basename(getvideo_dir.name)[len(tmpdir_opts["prefix"]):-len(tmpdir_opts["suffix"])]
    print([
      os.path.join(DIR, 'perform_getvideo'),
      *[str(p) for p in params.values()],
      replay_file.name,
      getvideo_dir.name,
      os.path.join(DIR, 'persist', name + '.log'),
    ])
    proc = Popen([
      os.path.join(DIR, 'perform_getvideo'),
      *[str(p) for p in params.values()],
      replay_file.name,
      getvideo_dir.name,
      os.path.join(DIR, 'persist', name + '.log'),
    ])
    web.header('Content-Type', 'text/plain')
    with open(os.path.join(DIR, 'persist', name + '.pickle'), 'wb') as f:
      pickle.dump(dict(**params, pid=proc.pid, expected=fps * dur, now=time.time()), f)
    return name


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
                  mapextjson = {
                    "cavernBorder": landres["cavernBorder"],
                    "height": landres["height"],
                    "length": landres["length"],
                    "objectPlacements": landres["objectPlacements"],
                    "waterHeight": landres["waterHeight"],
                    "width": landres["width"],
                    "texture": landres["texture"],
                    "unknown": landres["unknown"],
                  }
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
            logjson["mapData"] = mapextjson
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
        <input type="file" id="replay" name="replay" accept=".WAgame"/>
        <input type="submit" value="Submit" />
      </form>
    </body>
    </html>
    """


if __name__ == "__main__":
  web.running = False
  web.config.debug = os.getenv("DEBUG") == "1"
  app = web.application(urls, globals())
  app.run()
