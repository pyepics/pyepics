import epics.autosave
import time
epics.autosave.save_pvs('AutoSaveTest.req', 'tmp.sav')

time.sleep(0.5)
f = open('tmp.sav','r')

data  = f.read()

if len(data) > 50:
    print("AutoSave worked... data written to file 'tmp.sav'")
    
