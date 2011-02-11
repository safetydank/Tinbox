from nodebox.graphics.caironet import *
from nodebox.graphics import caironet

from nodebox.util import _copy_attr, _copy_attrs

__all__ = list(caironet.__all__)
__all__.extend(['Context'])

class Context(object):
    
    KEY_UP = 126
    KEY_DOWN = 125
    KEY_LEFT = 123
    KEY_RIGHT = 124
    KEY_BACKSPACE = 51
    
    def __init__(self, canvas=None, ns=None):

        """Initializes the context.
        
        Note that we have to give the namespace of the executing script, 
        which is a hack to keep the WIDTH and HEIGHT properties updated.
        Python's getattr only looks up property values once: at assign time."""

        if canvas is None:
            canvas = Canvas()
        if ns is None:
            ns = {}
        self.canvas = canvas
        self._ns = ns
        self._imagecache = {}
        self._vars = []
        self._resetContext()

    def _resetContext(self):
        self._outputmode = RGB
        self._colormode = RGB
        self._colorrange = 1.0
        self._fillcolor = self.Color()
        self._strokecolor = None
        self._strokewidth = 1.0
        self.canvas.background = self.Color(1.0)
        self._path = None
        self._autoclosepath = True
        self._transform = self.Transform()
        self._transformmode = CENTER
        self._transformstack = []
        self._fontname = "Helvetica"
        self._fontsize = 24
        self._lineheight = 1.2
        self._align = LEFT
        self._noImagesHint = False
        self._oldvars = self._vars
        self._vars = []

    def ximport(self, libName):
        lib = __import__(libName)
        self._ns[libName] = lib
        lib._ctx = self
        return lib
        
    ### Setup methods ###

    def size(self, width, height):
        self.canvas.width = width
        self.canvas.height = height
        self._ns["WIDTH"] = width
        self._ns["HEIGHT"] = height
        self.canvas._resize()

    def _get_width(self):
        return self.canvas.width

    WIDTH = property(_get_width)

    def _get_height(self):
        return self.canvas.height

    HEIGHT = property(_get_height)
    
    def speed(self, speed):
        self.canvas.speed = speed
        
    def background(self, *args):
        if len(args) > 0:
            if len(args) == 1 and args[0] is None:
                self.canvas.background = None
            else:
                self.canvas.background = self.Color(args)
        return self.canvas.background

    def outputmode(self, mode=None):
        if mode is not None:
            self._outputmode = mode
        return self._outputmode

    ### Variables ###

    def var(self, name, type, default=None, min=0, max=100, value=None):
        v = Variable(name, type, default, min, max, value)
        v = self.addvar(v)

    def addvar(self, v):
        oldvar = self.findvar(v.name)
        if oldvar is not None:
            if oldvar.compliesTo(v):
                v.value = oldvar.value
        self._vars.append(v)
        self._ns[v.name] = v.value

    def findvar(self, name):
        for v in self._oldvars:
            if v.name == name:
                return v
        return None

    ### Objects ####
    
    def _makeInstance(self, clazz, args, kwargs):
        """Creates an instance of a class defined in this document.        
           This method sets the context of the object to the current context."""
        inst = clazz(self, *args, **kwargs)
        return inst
    def BezierPath(self, *args, **kwargs):
        return self._makeInstance(BezierPath, args, kwargs)
    def ClippingPath(self, *args, **kwargs):
        return self._makeInstance(ClippingPath, args, kwargs)
    def Color(self, *args, **kwargs):
        return self._makeInstance(Color, args, kwargs)
#    def Image(self, *args, **kwargs):
#        return self._makeInstance(Image, args, kwargs)
    def Text(self, *args, **kwargs):
        return self._makeInstance(Text, args, kwargs)
    def Transform(self, *args, **kwargs):
        return self._makeInstance(Transform, args, kwargs)

    ### Primitives ###

    def rect(self, x, y, width, height, roundness=0.0, draw=True, **kwargs):
        BezierPath.checkKwargs(kwargs)
        if roundness == 0:
            p = self.BezierPath(**kwargs)
            p.rect(x, y, width, height)
        else:
            curve = min(width*roundness, height*roundness)
            p = self.BezierPath(**kwargs)
            p.moveto(x, y+curve)
            p.curveto(x, y, x, y, x+curve, y)
            p.lineto(x+width-curve, y)
            p.curveto(x+width, y, x+width, y, x+width, y+curve)
            p.lineto(x+width, y+height-curve)
            p.curveto(x+width, y+height, x+width, y+height, x+width-curve, y+height)
            p.lineto(x+curve, y+height)
            p.curveto(x, y+height, x, y+height, x, y+height-curve)
            p.closepath()
        p.inheritFromContext(kwargs.keys())

        if draw:
            p.draw()
        return p

    def oval(self, x, y, width, height, draw=True, **kwargs):
        BezierPath.checkKwargs(kwargs)
        path = self.BezierPath(**kwargs)
        path.oval(x, y, width, height)
        path.inheritFromContext(kwargs.keys())

        if draw:
          path.draw()
        return path

    def line(self, x1, y1, x2, y2, draw=True, **kwargs):
        BezierPath.checkKwargs(kwargs)
        p = self.BezierPath(**kwargs)
        p.line(x1, y1, x2, y2)
        p.inheritFromContext(kwargs.keys())
        if draw:
          p.draw()
        return p

    def star(self, startx, starty, points=20, outer= 100, inner = 50, draw=True, **kwargs):
        BezierPath.checkKwargs(kwargs)
        from math import sin, cos, pi

        p = self.BezierPath(**kwargs)
        p.moveto(startx, starty + outer)

        for i in range(1, int(2 * points)):
          angle = i * pi / points
          x = sin(angle)
          y = cos(angle)
          if i % 2:
              radius = inner
          else:
              radius = outer
          x = startx + radius * x
          y = starty + radius * y
          p.lineto(x,y)

        p.closepath()
        p.inheritFromContext(kwargs.keys())
        if draw:
          p.draw()
        return p

    def arrow(self, x, y, width=100, type=NORMAL, draw=True, **kwargs):

        """Draws an arrow.

        Draws an arrow at position x, y, with a default width of 100.
        There are two different types of arrows: NORMAL and trendy FORTYFIVE degrees arrows.
        When draw=False then the arrow's path is not ended, similar to endpath(draw=False)."""

        BezierPath.checkKwargs(kwargs)
        if type==NORMAL:
          return self._arrow(x, y, width, draw, **kwargs)
        elif type==FORTYFIVE:
          return self._arrow45(x, y, width, draw, **kwargs)
        else:
          raise NodeBoxError("arrow: available types for arrow() are NORMAL and FORTYFIVE\n")

    def _arrow(self, x, y, width, draw, **kwargs):

        head = width * .4
        tail = width * .2

        p = self.BezierPath(**kwargs)
        p.moveto(x, y)
        p.lineto(x-head, y+head)
        p.lineto(x-head, y+tail)
        p.lineto(x-width, y+tail)
        p.lineto(x-width, y-tail)
        p.lineto(x-head, y-tail)
        p.lineto(x-head, y-head)
        p.lineto(x, y)
        p.closepath()
        p.inheritFromContext(kwargs.keys())
        if draw:
          p.draw()
        return p

    def _arrow45(self, x, y, width, draw, **kwargs):

        head = .3
        tail = 1 + head

        p = self.BezierPath(**kwargs)
        p.moveto(x, y)
        p.lineto(x, y+width*(1-head))
        p.lineto(x-width*head, y+width)
        p.lineto(x-width*head, y+width*tail*.4)
        p.lineto(x-width*tail*.6, y+width)
        p.lineto(x-width, y+width*tail*.6)
        p.lineto(x-width*tail*.4, y+width*head)
        p.lineto(x-width, y+width*head)
        p.lineto(x-width*(1-head), y)
        p.lineto(x, y)
        p.inheritFromContext(kwargs.keys())
        if draw:
          p.draw()
        return p

    ### Path Commands ###

    def beginpath(self, x=None, y=None):
        self._path = self.BezierPath()
        self._pathclosed = False
        if x != None and y != None:
            self._path.moveto(x,y)

    def moveto(self, x, y):
        if self._path is None:
            raise NodeBoxError, "No current path. Use beginpath() first."
        self._path.moveto(x,y)

    def lineto(self, x, y):
        if self._path is None:
            raise NodeBoxError, "No current path. Use beginpath() first."
        self._path.lineto(x, y)

    def curveto(self, x1, y1, x2, y2, x3, y3):
        if self._path is None:
            raise NodeBoxError, "No current path. Use beginpath() first."
        self._path.curveto(x1, y1, x2, y2, x3, y3)

    def closepath(self):
        if self._path is None:
            raise NodeBoxError, "No current path. Use beginpath() first."
        if not self._pathclosed:
            self._path.closepath()

    def endpath(self, draw=True):
        if self._path is None:
            raise NodeBoxError, "No current path. Use beginpath() first."
        if self._autoclosepath:
            self.closepath()
        p = self._path
        p.inheritFromContext()
        if draw:
            p.draw()
        self._path = None
        self._pathclosed = False
        return p

    def drawpath(self, path, **kwargs):
        BezierPath.checkKwargs(kwargs)
        if isinstance(path, (list, tuple)):
            path = self.BezierPath(path, **kwargs)
        else: # Set the values in the current bezier path with the kwargs
            for arg_key, arg_val in kwargs.items():
                setattr(path, arg_key, _copy_attr(arg_val))
        path.inheritFromContext(kwargs.keys())
        path.draw()

    def autoclosepath(self, close=True):
        self._autoclosepath = close

    def findpath(self, points, curvature=1.0):
        import bezier
        path = bezier.findpath(points, curvature=curvature)
        path._ctx = self
        path.inheritFromContext()
        return path
    
    ### Clipping Commands ###
    
    def beginclip(self, path):
        cp = self.ClippingPath(path)
        self.canvas.push(cp)
        return cp

    def endclip(self):
        self.canvas.pop()

    ### Transformation Commands ###

    def push(self):
        self._transformstack.insert(0, self._transform.matrix)

    def pop(self):
        try:
            self._transform = self.Transform(self._transformstack[0])
            del self._transformstack[0]
        except IndexError, e:
            raise NodeBoxError, "pop: too many pops!"

    def transform(self, mode=None):
        if mode is not None:
            self._transformmode = mode
        return self._transformmode
        
    def translate(self, x, y):
        self._transform.translate(x, y)
        
    def reset(self):
        self._transform = self.Transform()

    def rotate(self, degrees=0, radians=0):
        self._transform.rotate(-degrees,-radians)

    def translate(self, x=0, y=0):
        self._transform.translate(x,y)

    def scale(self, x=1, y=None):
        self._transform.scale(x,y)

    def skew(self, x=0, y=0):
        self._transform.skew(x,y)

    ### Color Commands ###

    color = Color
    
    def colormode(self, mode=None, range=None):
        if mode is not None:
            self._colormode = mode
        if range is not None:
            self._colorrange = float(range)
        return self._colormode

    def colorrange(self, range=None):
        if range is not None:
            self._colorrange = float(range)
        return self._colorrange

    def nofill(self):
        self._fillcolor = None

    def fill(self, *args):
        if len(args) > 0:
            self._fillcolor = self.Color(*args)
        return self._fillcolor

    def nostroke(self):
        self._strokecolor = None

    def stroke(self, *args):
        if len(args) > 0:
            self._strokecolor = self.Color(*args)
        return self._strokecolor

    def strokewidth(self, width=None):
        if width is not None:
            self._strokewidth = max(width, 0.0001)
        return self._strokewidth

    ### Font Commands ###

    def font(self, fontname=None, fontsize = None):
        if fontname is not None:
            if not Text.font_exists(fontname):
                raise NodeBoxError, 'Font "%s" not found.' % fontname
            else:
                self._fontname = fontname
        if fontsize is not None:
            self._fontsize = fontsize
        return self._fontname

    def fontsize(self, fontsize=None):
        if fontsize is not None:
            self._fontsize = fontsize
        return self._fontsize

    def lineheight(self, lineheight=None):
        if lineheight is not None:
            self._lineheight = max(lineheight, 0.01)
        return self._lineheight

    def align(self, align=None):
        if align is not None:
            self._align = align
        return self._align

#    def textwidth(self, txt, width=None, **kwargs):
#        """Calculates the width of a single-line string."""
#        return self.textmetrics(txt, width, **kwargs)[0]
#
#    def textheight(self, txt, width=None, **kwargs):
#        """Calculates the height of a (probably) multi-line string."""
#        return self.textmetrics(txt, width, **kwargs)[1]
#
    def text(self, txt, x, y, width=None, height=None, outline=False, draw=True, **kwargs):
        Text.checkKwargs(kwargs)
        txt = self.Text(txt, x, y, width, height, **kwargs)
        txt.inheritFromContext(kwargs.keys())
        if outline:
          path = txt.path
          if draw:
              path.draw()
          return path
        else:
          if draw:
            txt.draw()
          return txt
#
#    def textpath(self, txt, x, y, width=None, height=None, **kwargs):
#        Text.checkKwargs(kwargs)
#        txt = self.Text(txt, x, y, width, height, **kwargs)
#        txt.inheritFromContext(kwargs.keys())
#        return txt.path
#
#    def textmetrics(self, txt, width=None, height=None, **kwargs):
#        txt = self.Text(txt, 0, 0, width, height, **kwargs)
#        txt.inheritFromContext(kwargs.keys())
#        return txt.metrics
#
#    ### Image commands ###
#
#    def image(self, path, x, y, width=None, height=None, alpha=1.0, data=None, draw=True, **kwargs):
#        img = self.Image(path, x, y, width, height, alpha, data=data, **kwargs)
#        img.inheritFromContext(kwargs.keys())
#        if draw:
#            img.draw()
#        return img
#
#    def imagesize(self, path, data=None):
#        img = self.Image(path, data=data)
#        return img.size
        
    ### Canvas proxy ###
    
    def save(self, fname, format=None):
        self.canvas.save(fname, format)

