from distutils.core import setup
import py2exe

setup(name="Python Instruments", 
      # console=[{'script': "EpicsInstrument.py", 'icon_resources': [(0, 'instrument.ico')]}],
      windows=[{'script': "EpicsInstrument.py", 'icon_resources': [(0, 'instrument.ico')]}],
      # windows=["run_stage.py"],
      options = dict(py2exe=dict(optimize=0,
                                 includes=['epics', 'ctypes', 'wx', 'sqlalchemy'],
                                 )
                     )
      )

