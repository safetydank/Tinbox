import nodebox.util.os as os
import nodebox.util.color as colorlib
from nodebox.util import _copy_attr, _copy_attrs
from math import pi, tan, sqrt

import sys, clr
sys.path.append(os.path.join(os.getcwd(), "cairo.net"))
clr.AddReferenceToFile("Mono.Cairo.dll")
import Cairo

__all__ = [
        "DEFAULT_WIDTH", "DEFAULT_HEIGHT",
        "inch", "cm", "mm",
        "RGB", "HSB", "CMYK",
        "CENTER", "CORNER",
        "MOVETO", "LINETO", "CURVETO", "CLOSE",
        "RECT",
        "LEFT", "RIGHT", "CENTER", "JUSTIFY",
        "NORMAL","FORTYFIVE",
        "NUMBER", "TEXT", "BOOLEAN","BUTTON",
        "NodeBoxError",
        "Point", "Grob", 
# "Image", "Variable", 
        "ClippingPath", "BezierPath", "PathElement", "Color", "Transform", "Canvas", "Text",
        ]

DEFAULT_WIDTH, DEFAULT_HEIGHT = 1000, 1000

inch = 72
cm = 28.3465
mm = 2.8346

RGB = "rgb"
HSB = "hsb"
CMYK = "cmyk"

CENTER = "center"
CORNER = "corner"

MOVETO  = 1
LINETO  = 2
CURVETO = 3
CLOSE   = 4
RECT    = 5

LEFT    = 1
RIGHT   = 2
CENTER  = 3
JUSTIFY = 4

NORMAL=1
FORTYFIVE=2

NUMBER = 1
TEXT = 2
BOOLEAN = 3
BUTTON = 4

_STATE_NAMES = {
    '_outputmode':    'outputmode',
    '_colorrange':    'colorrange',
    '_fillcolor':     'fill',
    '_strokecolor':   'stroke',
    '_strokewidth':   'strokewidth',
    '_transform':     'transform',
    '_transformmode': 'transformmode',
    '_fontname':      'font',
    '_fontsize':      'fontsize',
    '_align':         'align',
    '_lineheight':    'lineheight',
}

KAPPA = 4 * (sqrt(2) - 1) / 3

class NodeBoxError(Exception): pass

class Point(object):

    def __init__(self, *args):
        if len(args) == 2:
            self.x, self.y = args
        elif len(args) == 1:
            self.x, self.y = args[0]
        elif len(args) == 0:
            self.x = self.y = 0.0
        else:
            raise NodeBoxError, "Wrong initializer for Point object"

    def __repr__(self):
        return "Point(x=%.3f, y=%.3f)" % (self.x, self.y)
        
    def __eq__(self, other):
        if other is None: return False
        return self.x == other.x and self.y == other.y
        
    def __ne__(self, other):
        return not self.__eq__(other)


class Grob(object):
    """A GRaphic OBject is the base class for all DrawingPrimitives."""

    def __init__(self, ctx):
        """Initializes this object with the current context."""
        self._ctx = ctx

    def draw(self):
        """Appends the grob to the canvas.
           This will result in a draw later on, when the scene graph is rendered."""
        # XXX this kind of sucks, making a copy every time an element is drawn
        # need to come up with a better way of capturing context state
        self._ctx.canvas.append(self.copy())
        # print "draw called with transform: "+str(self._transform)
        
    def copy(self):
        """Returns a deep copy of this grob."""
        raise NotImplementedError, "Copy is not implemented on this Grob class."
        
    def inheritFromContext(self, ignore=()):
        attrs_to_copy = list(self.__class__.stateAttributes)
        [attrs_to_copy.remove(k) for k, v in _STATE_NAMES.items() if v in ignore]
        _copy_attrs(self._ctx, self, attrs_to_copy)
        
    def checkKwargs(self, kwargs):
        remaining = [arg for arg in kwargs.keys() if arg not in self.kwargs]
        if remaining:
            raise NodeBoxError, "Unknown argument(s) '%s'" % ", ".join(remaining)
    checkKwargs = classmethod(checkKwargs)

class TransformMixin(object):

    """Mixin class for transformation support.
    Adds the _transform and _transformmode attributes to the class."""
    
    def __init__(self):
        self._reset()
        
    def _reset(self):
        self._transform = Transform(self._ctx)
        self._transformmode = CENTER
        
    def _get_transform(self):
        return self._transform
    def _set_transform(self, transform):
        self._transform = Transform(self._ctx, transform)
    transform = property(_get_transform, _set_transform)
    
    def _get_transformmode(self):
        return self._transformmode
    def _set_transformmode(self, mode):
        self._transformmode = mode
    transformmode = property(_get_transformmode, _set_transformmode)
        
    def translate(self, x, y):
        self._transform.translate(x, y)
        
    def reset(self):
        self._transform = Transform(self._ctx)

    def rotate(self, degrees=0, radians=0):
        self._transform.rotate(-degrees,-radians)

    def translate(self, x=0, y=0):
        self._transform.translate(x,y)

    def scale(self, x=1, y=None):
        self._transform.scale(x,y)

    def skew(self, x=0, y=0):
        self._transform.skew(x,y)
        
class ColorMixin(object):
    
    """Mixin class for color support.
    Adds the _fillcolor, _strokecolor and _strokewidth attributes to the class."""

    def __init__(self, **kwargs):
        try:
            self._fillcolor = Color(self._ctx, kwargs['fill'])
        except KeyError:
            # XXX this should be set to None I think
            # self._fillcolor = Color(self._ctx)
            self._fillcolor = None
        try:
            self._strokecolor = Color(self._ctx, kwargs['stroke'])
        except KeyError:
            self._strokecolor = None
        self._strokewidth = kwargs.get('strokewidth', 1.0)
        
    def _get_fill(self):
        return self._fillcolor
    def _set_fill(self, *args):
        self._fillcolor = Color(self._ctx, *args)
    fill = property(_get_fill, _set_fill)
    
    def _get_stroke(self):
        return self._strokecolor
    def _set_stroke(self, *args):
        self._strokecolor = Color(self._ctx, *args)
    stroke = property(_get_stroke, _set_stroke)
    
    def _get_strokewidth(self):
        return self._strokewidth
    def _set_strokewidth(self, strokewidth):
        self._strokewidth = max(strokewidth, 0.0001)
    strokewidth = property(_get_strokewidth, _set_strokewidth)

class BezierPath(Grob, TransformMixin, ColorMixin):
    """A BezierPath """
    
    stateAttributes = ('_fillcolor', '_strokecolor', '_strokewidth', '_transform', '_transformmode')
    kwargs = ('fill', 'stroke', 'strokewidth')

    def __init__(self, ctx, path=None, **kwargs):
        super(BezierPath, self).__init__(ctx)
        TransformMixin.__init__(self)
        ColorMixin.__init__(self, **kwargs)

        self._segment_cache = None
        if path is None:
            self._elements = []
        elif isinstance(path, (list,tuple)):
            self._elements = []
            self.extend(path)
        elif isinstance(path, BezierPath):
            # XXX yeah yeah this sucks
            self._elements = []
            for p in path._elements:
                self._elements.append(p)
            _copy_attrs(path, self, self.stateAttributes)
        else:
            raise NodeBoxError, "Don't know what to do with %s." % path
            
    def copy(self):
        return self.__class__(self._ctx, self)

    ### Path methods ###

    def moveto(self, x, y):
        self._elements.append(PathElement(MOVETO, ((x,y),)))

    def lineto(self, x, y):
        self._elements.append(PathElement(LINETO, ((x,y),)))

    def curveto(self, x1, y1, x2, y2, x3, y3):
        self._elements.append(PathElement(CURVETO, ((x1,y1),(x2,y2),(x3,y3))))

    def closepath(self):
        self._elements.append(PathElement(CLOSE, None))

    def setlinewidth(self, width):
        self.linewidth = width

    def _get_bounds(self):
        try:
            context = self._ctx.canvas.cairoContext
            context.Save()
            self._execute(context)
            b = context.StrokeExtents()

            # it seems this is necessary to clear the path after execution
            # even though wrapped with a save/restore
            # i assume that cairo is smart enough to do a no-op if alpha=0
            context.Color = Cairo.Color(0,0,0,0)
            context.Stroke()

            context.Restore()
            # print "bounds are: %f %f %f %f"%(b.X, b.Y, b.Width, b.Height)
            return (b.X, b.Y) , (b.Width, b.Height)
        except:
            # print 'exception caught'
            # Path is empty -- no bounds
            return (0,0) , (0,0)

    bounds = property(_get_bounds)

    # def contains(self, x, y):
    #     return self._nsBezierPath.containsPoint_((x,y))
        
    ### Basic shapes ###
    
    def rect(self, x, y, width, height):
        self._segment_cache = None
        self._elements.append(PathElement(RECT, ((x,y),(width,height))))
        # self._nsBezierPath.appendBezierPathWithRect_( ((x, y), (width, height)) )
        
    def oval(self, x, y, width, height):
        self._segment_cache = None
        hdiff = width / 2 * KAPPA
        vdiff = height / 2 * KAPPA
        self.moveto(x + width/2, y + height)
        self.curveto(x + width/2 - hdiff, y + height, x, y + height/2 + vdiff, x, y + height/2)
        self.curveto(x, y + height/2 - vdiff, x + width/2 - hdiff, y, x + width/2, y)
        self.curveto(x + width/2 + hdiff, y, x + width, y + height/2 - vdiff, x + width, y + height/2)
        self.curveto(x + width, y + height/2 + vdiff, x + width/2 + hdiff, y + height, x + width/2, y + height)
        
    def line(self, x1, y1, x2, y2):
        self._segment_cache = None
        self.moveto(x1, y1)
        self.lineto(x2, y2)

    ### List methods ###

    def __getitem__(self, index):
        el = self._elements[index]
        return el.copy()

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    def __len__(self):
        return len(self._elements)

    def extend(self, pathElements):
        self._segment_cache = None
        for el in pathElements:
            if isinstance(el, (list, tuple)):
                x, y = el
                if len(self) == 0:
                    cmd = MOVETO
                else:
                    cmd = LINETO
                self.append(PathElement(cmd, ((x, y),)))
            elif isinstance(el, PathElement):
                self.append(el)
            else:
                raise NodeBoxError, "Don't know how to handle %s" % el

    def append(self, el):
        self._segment_cache = None
        if el.cmd == MOVETO:
            self.moveto(el.x, el.y)
        elif el.cmd == LINETO:
            self.lineto(el.x, el.y)
        elif el.cmd == CURVETO:
            self.curveto(el.ctrl1.x, el.ctrl1.y, el.ctrl2.x, el.ctrl2.y, el.x, el.y)
        elif el.cmd == CLOSE:
            self.closepath()
            
    def _get_contours(self):
        from nodebox.graphics import bezier
        return bezier.contours(self)
    contours = property(_get_contours)

    ### Drawing methods ###

    def _get_transform(self):
        trans = self._transform.copy()
        if (self._transformmode == CENTER):
            # XXX incorrect until bounds method is fixed
            (x, y), (w, h) = self.bounds
            deltax = x+w/2
            deltay = y+h/2
            t = Transform(self._ctx)
            t.translate(-deltax,-deltay)
            trans.prepend(t)
            t = Transform(self._ctx)
            t.translate(deltax,deltay)
            trans.append(t)
        return trans
    transform = property(_get_transform)

    def _draw(self):
        context = self._ctx.canvas.cairoContext

        context.Save()

        self.transform.concat()

        self._execute(context)

        if self._fillcolor and self._strokecolor:
            fill_method = context.FillPreserve
        else:
            fill_method = context.Fill

        if self._fillcolor:
            self._fillcolor.set()
            fill_method()

        if self._strokecolor:
            self._strokecolor.set()
            context.LineWidth = self._strokewidth
            context.Stroke()

        context.Restore()
    
    def _execute(self, context):
        for el in self._elements:
            el._execute(context)
        
    ### Mathematics ###
    
    def segmentlengths(self, relative=False, n=10):
        import bezier
        if relative: # Use the opportunity to store the segment cache.
            if self._segment_cache is None:
                self._segment_cache = bezier.segment_lengths(self, relative=True, n=n)
            return self._segment_cache
        else:
            return bezier.segment_lengths(self, relative=False, n=n)

    def _get_length(self, segmented=False, n=10):
        import bezier
        return bezier.length(self, segmented=segmented, n=n)
    length = property(_get_length)
        
    def point(self, t):
        import bezier
        return bezier.point(self, t)
        
    def points(self, amount=100):
        import bezier
        if len(self) == 0:
            raise NodeBoxError, "The given path is empty"

        # The delta value is divided by amount - 1, because we also want the last point (t=1.0)
        # If I wouldn't use amount - 1, I fall one point short of the end.
        # E.g. if amount = 4, I want point at t 0.0, 0.33, 0.66 and 1.0,
        # if amount = 2, I want point at t 0.0 and t 1.0
        try:
            delta = 1.0/(amount-1)
        except ZeroDivisionError:
            delta = 1.0

        for i in xrange(amount):
            yield self.point(delta*i)
            
    def addpoint(self, t):
        import bezier
        self._elements = bezier.insert_point(self, t)._elements
        self._segment_cache = None

class PathElement(object):
    def __init__(self, cmd=None, pts=None):
        self.cmd = cmd
        if cmd == MOVETO:
            assert len(pts) == 1
            self.x, self.y = pts[0]
            self.ctrl1 = Point(pts[0])
            self.ctrl2 = Point(pts[0])
        elif cmd == LINETO:
            assert len(pts) == 1
            self.x, self.y = pts[0]
            self.ctrl1 = Point(pts[0])
            self.ctrl2 = Point(pts[0])
        elif cmd == CURVETO:
            assert len(pts) == 3
            self.ctrl1 = Point(pts[0])
            self.ctrl2 = Point(pts[1])
            self.x, self.y = pts[2]
        elif cmd == RECT:
            assert len(pts) == 2
            self.x, self.y = pts[0]
            self.ctrl1 = Point(pts[1])
            self.ctrl2 = Point()
        elif cmd == CLOSE:
            assert pts is None or len(pts) == 0
            self.x = self.y = 0.0
            self.ctrl1 = Point(0.0, 0.0)
            self.ctrl2 = Point(0.0, 0.0)
        else:
            self.x = self.y = 0.0
            self.ctrl1 = Point()
            self.ctrl2 = Point()

    def __repr__(self):
        if self.cmd == MOVETO:
            return "PathElement(MOVETO, ((%.3f, %.3f),))" % (self.x, self.y)
        elif self.cmd == LINETO:
            return "PathElement(LINETO, ((%.3f, %.3f),))" % (self.x, self.y)
        elif self.cmd == CURVETO:
            return "PathElement(CURVETO, ((%.3f, %.3f), (%.3f, %s), (%.3f, %.3f))" % \
                (self.ctrl1.x, self.ctrl1.y, self.ctrl2.x, self.ctrl2.y, self.x, self.y)
        elif self.cmd == CLOSE:
            return "PathElement(CLOSE)"
            
    def __eq__(self, other):
        if other is None: return False
        if self.cmd != other.cmd: return False
        return self.x == other.x and self.y == other.y \
            and self.ctrl1 == other.ctrl1 and self.ctrl2 == other.ctrl2
        
    def __ne__(self, other):
        return not self.__eq__(other)

    def copy(self):
        el = PathElement()
        # XXX find a nicer way to copy myself
        el.cmd = self.cmd
        el.x = self.x
        el.y = self.y
        el.ctrl1 = Point(self.ctrl1.x, self.ctrl1.y)
        el.ctrl2 = Point(self.ctrl2.x, self.ctrl2.y)
        return el

    def _execute(self, context):
        """ execute our Cairo commands on the given cairo context """
        x, y, x1, y1, x2, y2 = (self.x, self.y, self.ctrl1.x, self.ctrl1.y, 
                                                self.ctrl2.x, self.ctrl2.y)

        # print "executing command: " + str(self)
        if self.cmd == MOVETO:
            context.MoveTo(x, y)
        elif self.cmd == LINETO:
            context.LineTo(x, y)
        elif self.cmd == CURVETO:
            context.CurveTo(x1, y1, x2, y2, x, y)
        elif self.cmd == CLOSE:
            context.ClosePath()
        elif self.cmd == RECT:
            context.Rectangle(x, y, x1, y1)

class ClippingPath(Grob):

    def __init__(self, ctx, path):
        self._ctx = ctx
        self.path = path
        self._grobs = []
        
    def append(self, grob):
        self._grobs.append(grob)
        
    def _draw(self):
        context = self._ctx.canvas.cairoContext

        context.Save()
        # cp = self.path.transform.transformBezierPath(self.path)
        # cp._nsBezierPath.addClip()

        self.path._execute(context)
        context.Clip()

        for grob in self._grobs:
            grob._draw()

        context.Restore()
    
    def copy(self):
        pass

class Color(object):

    def __init__(self, ctx, *args):
        self._ctx = ctx
        params = len(args)

        # Decompose the arguments into tuples. 
        if params == 1 and isinstance(args[0], tuple):
            args = args[0]
            params = len(args)

        if params == 1 and args[0] is None:
            clr = Cairo.Color(0, 0, 0, 0)
        elif params == 1 and isinstance(args[0], Color):
            if self._ctx._outputmode == RGB:
                clr = args[0]._rgb
            else:
                clr = args[0]._cmyk
        elif params == 1 and isinstance(args[0], Cairo.Color):
            clr = args[0]
        elif params == 1: # Gray, no alpha
            args = self._normalizeList(args)
            g, = args
            clr = Cairo.Color(g, g, g, 1)
        elif params == 2: # Gray and alpha
            args = self._normalizeList(args)
            g, a = args
            clr = Cairo.Color(g, g, g, a)
        elif params == 3 and self._ctx._colormode == RGB: # RGB, no alpha
            args = self._normalizeList(args)
            r,g,b = args
            clr = Cairo.Color(r, g, b, 1)
        elif params == 3 and self._ctx._colormode == HSB: # HSB, no alpha
            h, s, b = self._normalizeList(args)
            r, g, b = colorlib.hsv_to_rgb(h, s, b)
            clr = Cairo.Color(r, g, b, 1)
        elif params == 4 and self._ctx._colormode == RGB: # RGB and alpha
            args = self._normalizeList(args)
            r, g, b, a = args
            clr = Cairo.Color(r, g, b, a)
        elif params == 4 and self._ctx._colormode == HSB: # HSB and alpha
            h, s, b, a = self._normalizeList(args)
            r, g, b = colorlib.hsv_to_rgb(h, s, b)
            clr = Cairo.Color(r, g, b, a)
        elif params == 4 and self._ctx._colormode == CMYK: # CMYK, no alpha
            raise NodeBoxError('CMYK colorspace not yet supported')
            # args = self._normalizeList(args)
            # c, m, y, k  = args
            # clr = NSColor.colorWithDeviceCyan_magenta_yellow_black_alpha_(c, m, y, k, 1)
        elif params == 5 and self._ctx._colormode == CMYK: # CMYK and alpha
            raise NodeBoxError('CMYK colorspace not yet supported')
            # args = self._normalizeList(args)
            # c, m, y, k, a  = args
            # clr = NSColor.colorWithDeviceCyan_magenta_yellow_black_alpha_(c, m, y, k, a)
        else:
            clr = Cairo.Color(0, 0, 0, 1)

        #  XXX obviously the self._cmyk member is set incorrectly until we
        #  find a conversion method
        self._cmyk = clr
        self._rgb  = clr

    def __repr__(self):
        return "%s(%.3f, %.3f, %.3f, %.3f)" % (self.__class__.__name__, self.red,
                self.green, self.blue, self.alpha)

    def set(self):
        # print "setting color " + str(self)
        self._ctx.canvas.cairoContext.Color = self.cairoColor
    
    def _get_cairoColor(self):
        if self._ctx._outputmode == RGB:
            return self._rgb
        else:
            return self._cmyk
    cairoColor = property(_get_cairoColor)
        
    def copy(self):
        new = self.__class__(self._ctx)
        # this should copy because Cairo.Color is a struct
        new._rgb = self._rgb
        new._updateCmyk()
        return new

    def _updateCmyk(self):
        # XXX conversion required
        self._cmyk = self._rgb

    def _updateRgb(self):
        # XXX conversion required
        self._rgb = self._cmyk

#     def _get_hue(self):
#         return self._rgb.hueComponent()
#     def _set_hue(self, val):
#         val = self._normalize(val)
#         h, s, b, a = self._rgb.getHue_saturation_brightness_alpha_()
#         self._rgb = NSColor.colorWithDeviceHue_saturation_brightness_alpha_(val, s, b, a)
#         self._updateCmyk()
#     h = hue = property(_get_hue, _set_hue, doc="the hue of the color")
# 
#     def _get_saturation(self):
#         return self._rgb.saturationComponent()
#     def _set_saturation(self, val):
#         val = self._normalize(val)
#         h, s, b, a = self._rgb.getHue_saturation_brightness_alpha_()
#         self._rgb = NSColor.colorWithDeviceHue_saturation_brightness_alpha_(h, val, b, a)
#         self._updateCmyk()
#     s = saturation = property(_get_saturation, _set_saturation, doc="the saturation of the color")
# 
#     def _get_brightness(self):
#         return self._rgb.brightnessComponent()
#     def _set_brightness(self, val):
#         val = self._normalize(val)
#         h, s, b, a = self._rgb.getHue_saturation_brightness_alpha_()
#         self._rgb = NSColor.colorWithDeviceHue_saturation_brightness_alpha_(h, s, val, a)
#         self._updateCmyk()
#     v = brightness = property(_get_brightness, _set_brightness, doc="the brightness of the color")
# 
#     def _get_hsba(self):
#         return self._rgb.getHue_saturation_brightness_alpha_()
#     def _set_hsba(self, values):
#         val = self._normalize(val)
#         h, s, b, a = values
#         self._rgb = NSColor.colorWithDeviceHue_saturation_brightness_alpha_(h, s, b, a)
#         self._updateCmyk()
#     hsba = property(_get_hsba, _set_hsba, doc="the hue, saturation, brightness and alpha of the color")
 
    def _get_red(self):
        return self._rgb.R
    def _set_red(self, val):
        self._rgb.R = self._normalize(val)
        self._updateCmyk()
    r = red = property(_get_red, _set_red, doc="the red component of the color")

    def _get_green(self):
        return self._rgb.G
    def _set_green(self, val):
        self._rgb.G = self._normalize(val)
        self._updateCmyk()
    g = green = property(_get_green, _set_green, doc="the green component of the color")

    def _get_blue(self):
        return self._rgb.B
    def _set_blue(self, val):
        self._rgb.B = self._normalize(val)
        self._updateCmyk()
    b = blue = property(_get_blue, _set_blue, doc="the blue component of the color")

    def _get_alpha(self):
        return self._rgb.A
    def _set_alpha(self, val):
        self._rgb.A = self._normalize(val)
        self._updateCmyk()
    a = alpha = property(_get_alpha, _set_alpha, doc="the alpha component of the color")
 
    def _get_rgba(self):
        return (self.r, self.g, self.b, self.a)
    def _set_rgba(self, val):
        val = self._normalizeList(val)
        r, g, b, a = val
        self._rgb = Cairo.Color(r, g, b, a)
        self._updateCmyk()
    rgba = property(_get_rgba, _set_rgba, doc="the red, green, blue and alpha values of the color")
# 
#     def _get_cyan(self):
#         return self._cmyk.cyanComponent()
#     def _set_cyan(self, val):
#         val = self._normalize(val)
#         c, m, y, k, a = self.cmyka # self._cmyk.getCyan_magenta_yellow_black_alpha_()
#         self._cmyk = NSColor.colorWithDeviceCyan_magenta_yellow_black_alpha_(val, m, y, k, a)
#         self._updateRgb()
#     c = cyan = property(_get_cyan, _set_cyan, doc="the cyan component of the color")
# 
#     def _get_magenta(self):
#         return self._cmyk.magentaComponent()
#     def _set_magenta(self, val):
#         val = self._normalize(val)
#         c, m, y, k, a = self.cmyka # self._cmyk.getCyan_magenta_yellow_black_alpha_()
#         self._cmyk = NSColor.colorWithDeviceCyan_magenta_yellow_black_alpha_(c, val, y, k, a)
#         self._updateRgb()
#     m = magenta = property(_get_magenta, _set_magenta, doc="the magenta component of the color")
# 
#     def _get_yellow(self):
#         return self._cmyk.yellowComponent()
#     def _set_yellow(self, val):
#         val = self._normalize(val)
#         c, m, y, k, a = self.cmyka # self._cmyk.getCyan_magenta_yellow_black_alpha_()
#         self._cmyk = NSColor.colorWithDeviceCyan_magenta_yellow_black_alpha_(c, m, val, k, a)
#         self._updateRgb()
#     y = yellow = property(_get_yellow, _set_yellow, doc="the yellow component of the color")
# 
#     def _get_black(self):
#         return self._cmyk.blackComponent()
#     def _set_black(self, val):
#         val = self._normalize(val)
#         c, m, y, k, a = self.cmyka # self._cmyk.getCyan_magenta_yellow_black_alpha_()
#         self._cmyk = NSColor.colorWithDeviceCyan_magenta_yellow_black_alpha_(c, m, y, val, a)
#         self._updateRgb()
#     k = black = property(_get_black, _set_black, doc="the black component of the color")
# 
#     def _get_cmyka(self):
#         return (self._cmyk.cyanComponent(), self._cmyk.magentaComponent(), self._cmyk.yellowComponent(), self._cmyk.blackComponent(), self._cmyk.alphaComponent())
#     cmyka = property(_get_cmyka, doc="a tuple containing the CMYKA values for this color")
# 
#     def blend(self, otherColor, factor):
#         """Blend the color with otherColor with a factor; return the new color. Factor
#         is a float between 0.0 and 1.0.
#         """
#         if hasattr(otherColor, "color"):
#             otherColor = otherColor._rgb
#         return self.__class__(color=self._rgb.blendedColorWithFraction_ofColor_(
#                 factor, otherColor))
# 
    def _normalize(self, v):
        """Bring the color into the 0-1 scale for the current colorrange"""
        return v / self._ctx._colorrange

    def _normalizeList(self, lst):
        """Bring the color into the 0-1 scale for the current colorrange"""
        return map(lambda x:x / self._ctx._colorrange, lst)

color = Color

class Text(Grob, TransformMixin, ColorMixin):

    stateAttributes = ('_transform', '_transformmode', '_fillcolor', '_fontname', 
                       '_fontsize', '_align', '_lineheight')
    kwargs = ('fill', 'font', 'fontsize', 'align', 'lineheight')

    def __init__(self, ctx, text, x=0, y=0, width=None, height=None, **kwargs):
        super(Text, self).__init__(ctx)
        TransformMixin.__init__(self)
        ColorMixin.__init__(self, **kwargs)
        self.text = unicode(text)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self._fontname = kwargs.get('font', "Arial")
        # self._fontsize = kwargs.get('fontsize', 24)
        self._fontsize = kwargs.get('fontsize', 1.0)
        self._lineheight = max(kwargs.get('lineheight', 1.2), 0.01)
        self._align = kwargs.get('align', LEFT)

    def copy(self):
        new = self.__class__(self._ctx, self.text)
        _copy_attrs(self, new,
            ('x', 'y', 'width', 'height', '_transform', '_transformmode', 
            '_fillcolor', '_fontname', '_fontsize', '_align', '_lineheight'))
        return new
        
    def font_exists(cls, fontname):
        # Check if the font exists.
        # f = NSFont.fontWithName_size_(fontname, 12)
        # return f is not None
        # XXX need to check Font exists
        return True
    font_exists = classmethod(font_exists)

    # def _get_font(self):
    #     return NSFont.fontWithName_size_(self._fontname, self._fontsize)
    # font = property(_get_font)

    # def _getLayoutManagerTextContainerTextStorage(self, clr=None):
    #     if not clr: clr = Color(self._ctx)

    #     paraStyle = NSMutableParagraphStyle.alloc().init()
    #     paraStyle.setAlignment_(self._align)
    #     paraStyle.setLineBreakMode_(NSLineBreakByWordWrapping)
    #     paraStyle.setLineHeightMultiple_(self._lineheight)

    #     dict = {NSParagraphStyleAttributeName:paraStyle,
    #             NSForegroundColorAttributeName:clr,
    #             NSFontAttributeName:self.font}

    #     textStorage = NSTextStorage.alloc().initWithString_attributes_(self.text, dict)
    #     try:
    #         textStorage.setFont_(self.font)
    #     except ValueError:
    #         raise NodeBoxError("Text.draw(): font '%s' not available.\n" % self._fontname)
    #         return

    #     layoutManager = NSLayoutManager.alloc().init()
    #     textContainer = NSTextContainer.alloc().init()
    #     if self.width != None:
    #         textContainer.setContainerSize_((self.width,1000000))
    #         textContainer.setWidthTracksTextView_(False)
    #         textContainer.setHeightTracksTextView_(False)
    #     layoutManager.addTextContainer_(textContainer)
    #     textStorage.addLayoutManager_(layoutManager)
    #     return layoutManager, textContainer, textStorage

    def _draw(self):
        if self._fillcolor is None: return
        x, y = self.x, self.y

        print "Writing text %s font face %s size %d"%(self.text, self._fontname, self._fontsize)
        context = self._ctx.canvas.cairoContext

        context.Save()

        self._fillcolor.set()
        self.transform.concat()

        context.SelectFontFace(self._fontname, Cairo.FontSlant.Normal, Cairo.FontWeight.Normal)
        context.SetFontSize(self._fontsize)
        context.MoveTo(self.x, self.y)
        context.ShowText(self.text)

        context.Restore()

        # if self._fillcolor is None: return
        # layoutManager, textContainer, textStorage = self._getLayoutManagerTextContainerTextStorage(self._fillcolor.nsColor)
        # x,y = self.x, self.y
        # glyphRange = layoutManager.glyphRangeForTextContainer_(textContainer)
        # (dx, dy), (w, h) = layoutManager.boundingRectForGlyphRange_inTextContainer_(glyphRange, textContainer)
        # preferredWidth, preferredHeight = textContainer.containerSize()
        # if self.width is not None:
        #     if self._align == RIGHT:
        #         x += preferredWidth - w
        #     elif self._align == CENTER:
        #         x += preferredWidth/2 - w/2

        # _save()
        # # Center-mode transforms: translate to image center
        # if self._transformmode == CENTER:
        #     deltaX = w / 2
        #     deltaY = h / 2
        #     t = Transform()
        #     t.translate(x+deltaX, y-self.font.defaultLineHeightForFont()+deltaY)
        #     t.concat()
        #     self._transform.concat()
        #     layoutManager.drawGlyphsForGlyphRange_atPoint_(glyphRange, (-deltaX-dx,-deltaY-dy))
        # else:
        #     self._transform.concat()
        #     layoutManager.drawGlyphsForGlyphRange_atPoint_(glyphRange, (x-dx,y-dy-self.font.defaultLineHeightForFont()))
        # _restore()
        # return (w, h)

    # def _get_metrics(self):
    #     layoutManager, textContainer, textStorage = self._getLayoutManagerTextContainerTextStorage()
    #     glyphRange = layoutManager.glyphRangeForTextContainer_(textContainer)
    #     (dx, dy), (w, h) = layoutManager.boundingRectForGlyphRange_inTextContainer_(glyphRange, textContainer)
    #     return w,h
    # metrics = property(_get_metrics)

    def _get_path(self):
        return None
    #     layoutManager, textContainer, textStorage = self._getLayoutManagerTextContainerTextStorage()
    #     x, y = self.x, self.y
    #     glyphRange = layoutManager.glyphRangeForTextContainer_(textContainer)
    #     (dx, dy), (w, h) = layoutManager.boundingRectForGlyphRange_inTextContainer_(glyphRange, textContainer)
    #     preferredWidth, preferredHeight = textContainer.containerSize()
    #     if self.width is not None:
    #        if self._align == RIGHT:
    #            x += preferredWidth - w
    #        elif self._align == CENTER:
    #            x += preferredWidth/2 - w/2
    #     length = layoutManager.numberOfGlyphs()
    #     path = NSBezierPath.bezierPath()
    #     for glyphIndex in range(length):
    #         lineFragmentRect = layoutManager.lineFragmentRectForGlyphAtIndex_effectiveRange_(glyphIndex)
    #         layoutPoint = layoutManager.locationForGlyphAtIndex_(glyphIndex)
    #         # Here layoutLocation is the location (in container coordinates) where the glyph was laid out. 
    #         finalPoint = [lineFragmentRect[0][0][0],lineFragmentRect[0][0][1]]
    #         finalPoint[0] += layoutPoint[0] - dx
    #         finalPoint[1] += layoutPoint[1] - dy
    #         g = layoutManager.glyphAtIndex_(glyphIndex)
    #         if g == 0: continue
    #         path.moveToPoint_((finalPoint[0], -finalPoint[1]))
    #         path.appendBezierPathWithGlyph_inFont_(g, self.font)
    #         path.closePath()
    #     path = BezierPath(self._ctx, path)
    #     trans = Transform()
    #     trans.translate(x,y-self.font.defaultLineHeightForFont())
    #     trans.scale(1.0,-1.0)
    #     path = trans.transformBezierPath(path)
    #     path.inheritFromContext()
    #     return path
    path = property(_get_path)
    

class Transform(object):

    def __init__(self, ctx, transform=None):
        self._ctx = ctx
        if transform is None:
            transform = Cairo.Matrix()
        elif isinstance(transform, Transform):
            transform = transform._matrix.Clone()
        elif isinstance(transform, (list, tuple)):
            (xx, yx, xy, yy, x0, y0) = tuple(transform)
            transform = Cairo.Matrix(xx, yx, xy, yy, x0, y0)
        elif isinstance(transform, Cairo.Matrix):
            pass
        else:
            raise NodeBoxError, "Don't know how to handle transform %s." % transform
        self._matrix = transform
        
    def set(self):
        context = self._ctx.canvas.cairoContext
        context.Matrix = self._matrix

    def concat(self):
        context = self._ctx.canvas.cairoContext
        context.Transform(self._matrix)

    def copy(self):
        return self.__class__(self._ctx, self._matrix.Clone())

    def __repr__(self):
        return "<%s [%.3f %.3f %.3f %.3f %.3f %.3f]>" % ((self.__class__.__name__,)
                 + tuple(self))

    def __iter__(self):
        values = (self._matrix.Xx, self._matrix.Yx, self._matrix.Xy,
                  self._matrix.Yy, self._matrix.X0, self._matrix.Y0)
        for value in values:
            yield value

    def _get_matrix(self):
        return self._matrix.Clone()
    def _set_matrix(self, value):
        self._matrix = value
    matrix = property(_get_matrix, _set_matrix)

    def rotate(self, degrees=0, radians=0):
        if degrees:
            self._matrix.Rotate(degrees * pi / 180)
        else:
            self._matrix.Rotate(radians)

    def translate(self, x=0, y=0):
        self._matrix.Translate(x, y)

    def scale(self, x=1, y=None):
        if y is None:
            y = x
        self._matrix.Scale(x, y)

    def skew(self, x=0, y=0):
        x = pi * x / 180
        y = pi * y / 180
        t = Transform(self._ctx, (1, -tan(y), tan(x), 1, 0, 0))
        self.prepend(t)

    def invert(self):
        self._matrix.invert()

    def append(self, other):
        if isinstance(other, Transform):
            other = other._matrix
        self._matrix.Multiply(other)

    def prepend(self, other):
        if isinstance(other, Transform):
            other = other._matrix
        self._matrix = Cairo.Matrix.Multiply(other, self._matrix)

    def transformPoint(self, point):
        (rx, ry) = (point.x, point.y)
        self._matrix.TransformPoint(rx, ry)
        return (rx, ry)

#    def transformBezierPath(self, path):
#        if isinstance(path, BezierPath):
#            path = BezierPath(path._ctx, path)
#        else:
#            raise NodeBoxError, "Can only transform BezierPaths"
#        path._nsBezierPath = self._nsAffineTransform.transformBezierPath_(path._nsBezierPath)
#        return path


class Canvas(Grob):

    def __init__(self, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        self.width = width
        self.height = height
        self.speed = None
        self.mousedown = False
        self.clear()

        self._resize()

    def _resize(self):
        self._dispose()

        # Create cairo context
        self._image = Cairo.ImageSurface(Cairo.Format.Argb32, self.width, self.height)
        self._context = Cairo.Context(self._image)

    def _dispose(self):
        pass
        if hasattr(self, '_image') and self._image:
            self._image.Destroy()
        if hasattr(self, '_context') and self._context:
            self._context.Dispose(True)

    def _getCairoImage(self):
        return self._image
    cairoImage = property(_getCairoImage)

    def _getCairoContext(self):
        return self._context
    cairoContext = property(_getCairoContext)

    def clear(self):
        self._grobs = self._container = []
        self._grobstack = [self._grobs]
        
    def _get_size(self):
        return self.width, self.height
    def _set_size(self, w, h):
        self.width  = width
        self.height = height
        self._resize
    size = property(_get_size, _set_size)

    def append(self, el):
        self._container.append(el)
        
    def __iter__(self):
        for grob in self._grobs:
            yield grob
            
    def __len__(self):
        return len(self._grobs)
        
    def __getitem__(self, index):
        return self._grobs[index]
        
    def push(self, containerGrob):
        self._grobstack.insert(0, containerGrob)
        self._container.append(containerGrob)
        self._container = containerGrob
        
    def pop(self):
        try:
            del self._grobstack[0]
            self._container = self._grobstack[0]
            return self._container
        except IndexError, e:
            raise NodeBoxError, "pop: too many canvas pops!"

    def draw(self):
        if self.background is not None:
            self.background.set()
            self.cairoContext.Rectangle(0, 0, self.width, self.height)
            self.cairoContext.Fill()
        for grob in self._grobs:
            grob._draw()
            
    def _getImageData(self, format):
        # if format == 'pdf':
        #     view = _PDFRenderView.alloc().initWithCanvas_(self)
        #     return view.dataWithPDFInsideRect_(view.bounds())
        # else:
        #     imgTypes = {"gif":  NSGIFFileType,
        #                 "jpg":  NSJPEGFileType,
        #                 "jpeg":  NSJPEGFileType,
        #                 "png":  NSPNGFileType,
        #                 "tiff": NSTIFFFileType}
        #     if format not in imgTypes:
        #         raise NodeBoxError, "Filename should end in .pdf, .tiff, .gif, .jpg or .png"
        #     data = self._nsImage.TIFFRepresentation()
        #     if format != 'tiff':
        #         imgType = imgTypes[format]
        #         rep = NSBitmapImageRep.imageRepWithData_(data)
        #         return rep.representationUsingType_properties_(imgType, None)
        #     else:
        #         return data
        return None

    def save(self, fname, format=None):
        if format is None:
            basename, ext = os.path.splitext(fname)
            format = ext[1:].lower() # Skip the dot
        # data = self._getImageData(format)
        # fname = NSString.stringByExpandingTildeInPath(fname)
        # data.writeToFile_atomically_(fname, False)

        # XXX only write to PNG for now
        self.draw()
        self.cairoImage.WriteToPng(fname)

