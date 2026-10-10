"""Run the normal suite and expose failures as CI annotations, without private inputs."""
import os
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.chdir(ROOT)
suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_*.py')
result=unittest.TextTestRunner(verbosity=1).run(suite)
if os.environ.get('GITHUB_ACTIONS')=='true':
 for test,trace in result.failures+result.errors:
  title=str(test).replace('%','%25').replace('\r','%0D').replace('\n','%0A').replace(',','%2C').replace(':','%3A')
  message=trace.replace('%','%25').replace('\r','%0D').replace('\n','%0A')
  print('::error title='+title+'::'+message,flush=True)
sys.exit(0 if result.wasSuccessful() else 1)
