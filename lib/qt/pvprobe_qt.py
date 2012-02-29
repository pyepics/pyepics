#!/usr/bin/env python

import epics
import sys
from PySide.QtGui import QWidget, QLabel, QLineEdit, QGridLayout, QApplication

class PVProbe(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setWindowTitle("PySide PV Probe:")

        self.pvname = QLineEdit()
        self.pvname.returnPressed.connect(self.onPVNameReturn)
        self.value  = QLabel(" ")
        self.pv = None
        
        grid = QGridLayout()
        grid.addWidget(QLabel("PV Name:"),   0, 0)
        grid.addWidget(QLabel("PV Value:"),  1, 0)
        grid.addWidget(self.pvname,  0, 1)
        grid.addWidget(self.value,   1, 1)

        self.setLayout(grid)

    def onPVNameReturn(self):
        self.pv = epics.PV(self.pvname.text(), callback=self.onPVChange)

    def onPVChange(self, pvname=None, char_value=None, **kw):
        self.value.setText(char_value)
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    probe = PVProbe()
    probe.show()
    sys.exit(app.exec_())
