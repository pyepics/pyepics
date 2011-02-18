"""
wx OGL (2d graphics library) utility functions for Epics and wxPython interaction
"""
import wx
import wx.lib.ogl as ogl
from wxlib import pvMixin


"""
   Mixin for any Shape that has PV callback support
"""
class pvShapeMixin(pvMixin):
    def __init__(self, pv=None, pvname=None):        
        pvMixin.__init__(self, pv, pvname)
        self.brushTranslations = {}
        self.penTranslations = {}
        self.shownTranslations = {}
        
    """
    Set a dictionary of value->brush translations that will be set automatically
    when the PV value changes. The brush is used to paint the shape foreground
    """
    def SetBrushTranslations(self, translations):
        self.brushTranslations = translations

    """
    Set a dictionary of value->bpen translations that will be set automatically
    when the PV value changes. The pen is used to paint the shape outline
    """
    def SetPenTranslations(self, translations):
        self.penTranslations = translations
        

    """
    Set a dictionary of value->boolean 'Shown' translations that will be set automatically
    when the PV value changes. The pen is used to show/hide the shape
    """
    def SetShownTranslations(self, translations):
        self.shownTranslations = translations


    def OnPVChange(self, raw_value):
        if raw_value in self.brushTranslations:
            self.SetBrush(self.brushTranslations[raw_value])            
        if raw_value in self.penTranslations:
            self.SetPen(self.penTranslations[raw_value])
        if raw_value in self.shownTranslations:
            self.Show(self.shownTranslations[raw_value])
        self.PVChanged(raw_value)
        self.Invalidate()

    """
    Override this method if you want your shape to do any special processing when the
    PV changes
    """
    def PVChanged(self, raw_value):
        pass


    """ Invalidate the shape's area on the parent shape canvas
        (convenience method)
    """
    def Invalidate(self):
        (w,h) = self.GetBoundingBoxMax()        
        x = self.GetX()
        y = self.GetY()
        self.GetCanvas().RefreshRect((x-w/2,y-h/2,w,h))
        

"""
  A RectangleShape which is attached to a particular PV value
"""
class pvRectangle(ogl.RectangleShape, pvShapeMixin):
    def __init__(self, w, h, pv=None, pvname=None):
        ogl.RectangleShape.__init__(self, w, h)
        pvShapeMixin.__init__(self, pv, pvname)

"""
   A CircleShape which is attached to a particular PVvalue
"""
class pvCircle(ogl.CircleShape, pvShapeMixin):
    def __init__(self, diameter, pv=None, pvname=None):
        ogl.CircleShape.__init__(self, diameter)
        pvShapeMixin.__init__(self, pv, pvname)

