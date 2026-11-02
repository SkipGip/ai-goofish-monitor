"""Background entry point for the per-user Windows scheduled task."""
import os
import runpy
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
os.chdir(root)
os.environ['PYTHONUTF8'] = '1'
(root / 'logs').mkdir(exist_ok=True)
# pythonw has no console streams; initialize them before importing the app.
sys.stdout = open(root / 'logs' / 'server-out.log', 'a', encoding='utf-8', buffering=1)
sys.stderr = open(root / 'logs' / 'server-error.log', 'a', encoding='utf-8', buffering=1)
runpy.run_path(str(root / 'run-local.py'), run_name='__main__')
