from jinja2 import Environment, FileSystemLoader
import traceback, sys
env = Environment(loader=FileSystemLoader('templates'))
try:
    env.get_template('play.html')
    print('Template compiled successfully')
except Exception:
    traceback.print_exc()
    sys.exit(1)
