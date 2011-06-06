from distutils.core import setup
import py2exe

setup(name="XRM Sample Stage", 
      # console=[{'script': "run_stage.py", 'icon_resources': [(0, 'micro.ico')]}],
      windows=[{'script': "run_stage.py", 'icon_resources': [(0, 'micro.ico')]}],
      options = dict(py2exe=dict(optimize=0,
                                 includes=['epics', 'ctypes', 'wx'])
                     ))

