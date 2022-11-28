#!/usr/bin/env python

import epics
import sys
try:
    from PySide.QtGui import QWidget, QLabel, QLineEdit, QGridLayout, QApplication
except:
    from PyQt4.QtGui import QWidget, QLabel, QLineEdit, QGridLayout, QApplication

from epics.utils import bytes2str

class PVText(QLabel):
    def __init__(self, pvname,  **kws):
        QLabel.__init__(self, '', **kws)
        self.pv = None
        self.cb_index = None

    def SetPV(self, pvname):
        if self.pv is not None and self.cb_index is not None:
            self.pv.remove_callback(self.cb_index)

        self.pv = epics.PV(bytes2str(pvname))
        self.setText(self.pv.get(as_string=True))
        self.cb_index = self.pv.add_callback(self.onPVChange)

    def onPVChange(self, pvname=None, char_value=None, **kws):
        self.setText(char_value)

class PVLineEdit(QLineEdit):
    def __init__(self, pvname=None,  **kws):
        QLineEdit.__init__(self, **kws)
        self.returnPressed.connect(self.onReturn)
        self.pv = None
        self.cb_index = None
        if pvname is not None:
            self.SetPV(pvname)

    def SetPV(self, pvname):
        if self.pv is not None and self.cb_index is not None:
            self.pv.remove_callback(self.cb_index)

        self.pv = epics.PV(bytes2str(pvname))
        self.cb_index = self.pv.add_callback(self.onPVChange)

    def onPVChange(self, pvname=None, char_value=None, **kws):
        self.setText(char_value)

    def onReturn(self):
        self.pv.put(bytes2str(self.text()))

class PVProbe(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setWindowTitle("PyQt4 PV Probe:")

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
        self.value.SetPV(self.pv1name.text())

    def onPV2NameReturn(self):
        self.pvedit.SetPV(self.pv2name.text())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    probe = PVProbe()
    probe.show()
    sys.exit(app.exec_())
