"""
wx OGL (2d graphics library) utility functions for Epics and wxPython
interaction

OGL is a (somewhat old-fashioned) 2D drawing library included with wxPython.
There are probably newer/better drawing libraries, but OGL works quite well
for drawing simple shapes or bitmaps.

"""
import wx.lib.ogl as ogl
from .wxlib import PVMixin

class PVShapeMixin(PVMixin):
    """
    Mixin for any Shape that has PV callback support

    """
    def __init__(self, pv=None, pvname=None):
        PVMixin.__init__(self, pv, pvname)
        self.brushTranslations = {}
        self.penTranslations = {}
        self.shownTranslations = {}

    def SetBrushTranslations(self, translations):
        """
        Set a dictionary of value->brush translations that will be set automatically
        when the PV value changes. The brush is used to paint the shape foreground

        The argument should be a dictionary with keys as PV values (string if available), and values
        as wx.Brush instances.

        """
        self.brushTranslations = translations

    def SetPenTranslations(self, translations):
        """
        Set a dictionary of value->bpen translations that will be set automatically
        when the PV value changes. The pen is used to paint the shape outline.

        The argument should be a dictionary with keys as PV values (string if available), and values
        as wx.Brush instances.

        """
        self.penTranslations = translations


    def SetShownTranslations(self, translations):
        """
        Set a dictionary of value->boolean 'Shown' translations that will be set automatically
        when the PV value changes. The value is used to show/hide the shape.

        """
        self.shownTranslations = translations


    def OnPVChange(self, raw_value):
        """
        Do not override this method, override PVChanged if you would like to do any
        custom callback behaviour

        """
        if raw_value in self.brushTranslations:
            self.SetBrush(self.brushTranslations[raw_value])
        if raw_value in self.penTranslations:
            self.SetPen(self.penTranslations[raw_value])
        if raw_value in self.shownTranslations:
            self.Show(self.shownTranslations[raw_value])
        self.PVChanged(raw_value)
        self.Invalidate()

    def PVChanged(self, raw_value):
        """
        Override this method if you want your shape to do any special processing when the
        PV changes

        Note that the shape will be automatically invalidated (redrawn) after this method is called.

        """
        pass


    def Invalidate(self):
        """
        Invalidate the shape's area on the parent shape canvas to cause a redraw
        (convenience method)

        """
        (w, h) = self.GetBoundingBoxMax()
        x = self.GetX()
        y = self.GetY()
        self.GetCanvas().RefreshRect((x-w/2, y-h/2, w, h))


class PVRectangle(ogl.RectangleShape, PVShapeMixin):
    """
    A RectangleShape which is associated with a particular PV value

    """
    def __init__(self, w, h, pv=None, pvname=None):
        ogl.RectangleShape.__init__(self, w, h)
        PVShapeMixin.__init__(self, pv, pvname)

class PVCircle(ogl.CircleShape, PVShapeMixin):
    """
    A CircleShape which is associated with a particular PV value

    """
    def __init__(self, diameter, pv=None, pvname=None):
        ogl.CircleShape.__init__(self, diameter)
        PVShapeMixin.__init__(self, pv, pvname)
