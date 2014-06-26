#!/usr/bin/env python

import epics
import sys
from PySide.QtGui import QWidget, QLabel, QLineEdit, QGridLayout, QApplication

class PVText(QLabel):
    def __init__(self, pvname,  **kws):
        QLabel.__init__(self, '', **kws)
        
    def SetPV(self, pvname):
        self.pv = epics.PV(pvname, callback=self.onPVChange)

    def onPVChange(self, pvname=None, char_value=None, **kws):
        self.setText(char_value)
        
class PVLineEdit(QLineEdit):
    def __init__(self, pvname=None,  **kws):
        QLineEdit.__init__(self, **kws)
        self.returnPressed.connect(self.onReturn)
        if pvname is not None:
            self.SetPV(pvname)
        
    def SetPV(self, pvname):
        self.pv = epics.PV(pvname, callback=self.onPVChange)

    def onPVChange(self, pvname=None, char_value=None, **kws):
        self.setText(char_value)

    def onReturn(self):
        self.pv.put(self.text())
        
class PVProbe(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setWindowTitle("PySide PV Probe:")

        self.pv1name = QLineEdit()
        self.pv2name = QLineEdit()
        self.value   = PVText(None)
        self.pvedit  = PVLineEdit()
        
        grid = QGridLayout()
        grid.addWidget(QLabel("PV1 Name (Read-only):"),   0, 0)
        grid.addWidget(QLabel("PV1 Value (Read-only):"),  1, 0)
        grid.addWidget(QLabel("PV2 Name: (Read-write):"), 2, 0)
        grid.addWidget(QLabel("PV2 Value (Read-write):"), 3, 0)
        grid.addWidget(self.pv1name,  0, 1)
        grid.addWidget(self.value,    1, 1)
        grid.addWidget(self.pv2name,  2, 1)
        grid.addWidget(self.pvedit,   3, 1)

        self.pv1name.returnPressed.connect(self.onPV1NameReturn)
        self.pv2name.returnPressed.connect(self.onPV2NameReturn)

        self.setLayout(grid)

    def onPV1NameReturn(self):
        print(" PV Value set with", self.pv1name.text())
        print()
        self.value.SetPV(self.pv1name.text())
        
    def onPV2NameReturn(self):
        self.pvedit.SetPV(self.pv2name.text())
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    probe = PVProbe()
    probe.show()
    sys.exit(app.exec_())
