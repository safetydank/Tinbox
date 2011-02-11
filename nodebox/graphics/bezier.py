# Bezier - last updated for NodeBox 1.8.3
# Author: Tom De Smedt <tomdesmedt@trapdoor.be>
# Manual: http://nodebox.net/code/index.php/Bezier
# Copyright (c) 2007 by Tom De Smedt.
# Refer to the "Use" section on http://nodebox.net/code
# Thanks to Dr. Florimond De Smedt at the Free University of Brussels for the math routines.

from nodebox.graphics import BezierPath, PathElement, NodeBoxError, Point, MOVETO, LINETO, CURVETO, CLOSE

try:
    from cPathmatics import linepoint, linelength, curvepoint, curvelength
except:
    from pathmatics import linepoint, linelength, curvepoint, curvelength
    
def segment_lengths(path, relative=False, n=20):
    """Returns a list with the lengths of each segment in the path.
    
    >>> path = BezierPath(None)
    >>> segment_lengths(path)
    []
    >>> path.moveto(0, 0)
    >>> segment_lengths(path)
    []
    >>> path.lineto(100, 0)
    >>> segment_lengths(path)
    [100.0]
    >>> path.lineto(100, 300)
    >>> segment_lengths(path)
    [100.0, 300.0]
    >>> segment_lengths(path, relative=True)
    [0.25, 0.75]
    >>> path = BezierPath(None)
    >>> path.moveto(1, 2)
    >>> path.curveto(3, 4, 5, 6, 7, 8)
    >>> segment_lengths(path)
    [8.4852813742385695]
    """

    lengths = []
    first = True

    for el in path:
        if first == True:
            close_x, close_y = el.x, el.y
            first = False
        elif el.cmd == MOVETO:
            close_x, close_y = el.x, el.y
            lengths.append(0.0)
        elif el.cmd == CLOSE:
            lengths.append(linelength(x0, y0, close_x, close_y))
        elif el.cmd == LINETO:
            lengths.append(linelength(x0, y0, el.x, el.y))
        elif el.cmd == CURVETO:
            x3, y3, x1, y1, x2, y2 = el.x, el.y, el.ctrl1.x, el.ctrl1.y, el.ctrl2.x, el.ctrl2.y
            lengths.append(curvelength(x0, y0, x1, y1, x2, y2, x3, y3, n))
            
        if el.cmd != CLOSE:
            x0 = el.x
            y0 = el.y

    if relative:
        length = sum(lengths)
        try:
            return map(lambda l: l / length, lengths)
        except ZeroDivisionError: # If the length is zero, just return zero for all segments
            return [0.0] * len(lengths)
    else:
        return lengths

def length(path, segmented=False, n=20):

    """Returns the length of the path.

    Calculates the length of each spline in the path,
    using n as a number of points to measure.

    When segmented is True, returns a list
    containing the individual length of each spline
    as values between 0.0 and 1.0,
    defining the relative length of each spline
    in relation to the total path length.
    
    The length of an empty path is zero:
    >>> path = BezierPath(None)
    >>> length(path)
    0.0

    >>> path.moveto(0, 0)
    >>> path.lineto(100, 0)
    >>> length(path)
    100.0

    >>> path.lineto(100, 100)
    >>> length(path)
    200.0

    # Segmented returns a list of each segment
    >>> length(path, segmented=True)
    [0.5, 0.5]
    """

    if not segmented:
        return sum(segment_lengths(path, n=n), 0.0)
    else:
        return segment_lengths(path, relative=True, n=n)

def _locate(path, t, segments=None):
    
    """Locates t on a specific segment in the path.
    
    Returns (index, t, PathElement)
    
    A path is a combination of lines and curves (segments).
    The returned index indicates the start of the segment
    that contains point t.
    
    The returned t is the absolute time on that segment,
    in contrast to the relative t on the whole of the path.
    The returned point is the last MOVETO,
    any subsequent CLOSETO after i closes to that point.
    
    When you supply the list of segment lengths yourself,
    as returned from length(path, segmented=True),
    point() works about thirty times faster in a for-loop,
    since it doesn't need to recalculate the length
    during each iteration. Note that this has been deprecated:
    the BezierPath now caches the segment lengths the moment you use
    them.
    
    >>> path = BezierPath(None)
    >>> _locate(path, 0.0)
    Traceback (most recent call last):
        ...
    NodeBoxError: The given path is empty
    >>> path.moveto(0,0)
    >>> _locate(path, 0.0)
    Traceback (most recent call last):
        ...
    NodeBoxError: The given path is empty
    >>> path.lineto(100, 100)
    >>> _locate(path, 0.0)
    (0, 0.0, Point(x=0.0, y=0.0))
    >>> _locate(path, 1.0)
    (0, 1.0, Point(x=0.0, y=0.0))
    """
    
    if segments == None:
        segments = path.segmentlengths(relative=True)
        
    if len(segments) == 0:
        raise NodeBoxError, "The given path is empty"
    
    for i, el in enumerate(path):
        if i == 0 or el.cmd == MOVETO:
            closeto = Point(el.x, el.y)
        if t <= segments[i] or i == len(segments)-1: break
        else: t -= segments[i]

    try: t /= segments[i]
    except ZeroDivisionError: pass
    if i == len(segments)-1 and segments[i] == 0: i -= 1
    
    return (i, t, closeto)

def point(path, t, segments=None):

    """Returns coordinates for point at t on the path.

    Gets the length of the path, based on the length
    of each curve and line in the path.
    Determines in what segment t falls.
    Gets the point on that segment.
    
    When you supply the list of segment lengths yourself,
    as returned from length(path, segmented=True),
    point() works about thirty times faster in a for-loop,
    since it doesn't need to recalculate the length
    during each iteration. Note that this has been deprecated:
    the BezierPath now caches the segment lengths the moment you use
    them.
    
    >>> path = BezierPath(None)
    >>> point(path, 0.0)
    Traceback (most recent call last):
        ...
    NodeBoxError: The given path is empty
    >>> path.moveto(0, 0)
    >>> point(path, 0.0)
    Traceback (most recent call last):
        ...
    NodeBoxError: The given path is empty
    >>> path.lineto(100, 0)
    >>> point(path, 0.0)
    PathElement(LINETO, ((0.0, 0.0),))
    >>> point(path, 0.1)
    PathElement(LINETO, ((10.0, 0.0),))
    """

    if len(path) == 0:
        raise NodeBoxError, "The given path is empty"

    i, t, closeto = _locate(path, t, segments=segments)

    x0, y0 = path[i].x, path[i].y
    p1 = path[i+1]

    if p1.cmd == CLOSE:
        x, y = linepoint(t, x0, y0, closeto.x, closeto.y)
        return PathElement(LINETO, ((x, y),))
    elif p1.cmd == LINETO:
        x1, y1 = p1.x, p1.y
        x, y = linepoint(t, x0, y0, x1, y1)
        return PathElement(LINETO, ((x, y),))
    elif p1.cmd == CURVETO:
        x3, y3, x1, y1, x2, y2 = p1.x, p1.y, p1.ctrl1.x, p1.ctrl1.y, p1.ctrl2.x, p1.ctrl2.y
        x, y, c1x, c1y, c2x, c2y = curvepoint(t, x0, y0, x1, y1, x2, y2, x3, y3)
        return PathElement(CURVETO, ((c1x, c1y), (c2x, c2y), (x, y)))
    else:
        raise NodeBoxError, "Unknown cmd for p1 %s" % p1
        
def points(path, amount=100):
    """Returns an iterator with a list of calculated points for the path.
    This method calls the point method <amount> times, increasing t,
    distributing point spacing linearly.

    >>> path = BezierPath(None)
    >>> list(points(path))
    Traceback (most recent call last):
        ...
    NodeBoxError: The given path is empty
    >>> path.moveto(0, 0)
    >>> list(points(path))
    Traceback (most recent call last):
        ...
    NodeBoxError: The given path is empty
    >>> path.lineto(100, 0)
    >>> list(points(path, amount=4))
    [PathElement(LINETO, ((0.0, 0.0),)), PathElement(LINETO, ((25.0, 0.0),)), PathElement(LINETO, ((50.0, 0.0),)), PathElement(LINETO, ((75.0, 0.0),))]
    """

    if len(path) == 0:
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
        yield point(path, delta*i)

def contours(path):
    """Returns a list of contours in the path.
    
    A contour is a sequence of lines and curves
    separated from the next contour by a MOVETO.
    
    For example, the glyph "o" has two contours:
    the inner circle and the outer circle.

    >>> path = BezierPath(None)
    >>> path.moveto(0, 0)
    >>> path.lineto(100, 100)
    >>> len(contours(path))
    1
    
    A new contour is defined as something that starts with a moveto:
    >>> path.moveto(50, 50)
    >>> path.curveto(150, 150, 50, 250, 80, 95)
    >>> len(contours(path))
    2

    Empty moveto's don't do anything:
    >>> path.moveto(50, 50) 
    >>> path.moveto(50, 50)
    >>> len(contours(path))
    2
    
    It doesn't matter if the path is closed or open:
    >>> path.closepath()
    >>> len(contours(path))
    2
    """
    contours = []
    current_contour = None
    empty = True
    for i, el in enumerate(path):
        if el.cmd == MOVETO:
            if not empty:
                contours.append(current_contour)
            current_contour = BezierPath(path._ctx)
            current_contour.moveto(el.x, el.y)
            empty = True
        elif el.cmd == LINETO:
            empty = False
            current_contour.lineto(el.x, el.y)
        elif el.cmd == CURVETO:
            empty = False
            current_contour.curveto(el.ctrl1.x, el.ctrl1.y,
                el.ctrl2.x, el.ctrl2.y, el.x, el.y)
        elif el.cmd == CLOSE:
            current_contour.closepath()
    if not empty:
        contours.append(current_contour)
    return contours
    
def findpath(points, curvature=1.0):
    
    """Constructs a path between the given list of points.
    
    Interpolates the list of points and determines
    a smooth bezier path betweem them.
    
    The curvature parameter offers some control on
    how separate segments are stitched together:
    from straight angles to smooth curves.
    Curvature is only useful if the path has more than  three points.
    """
    
    # The list of points consists of Point objects,
    # but it shouldn't crash on something straightforward
    # as someone supplying a list of (x,y)-tuples.
    
    for i, pt in enumerate(points):
        if type(pt) == tuple:
            points[i] = Point(pt[0], pt[1])
    
    if len(points) == 0: return None
    if len(points) == 1:
        path = BezierPath(None)
        path.moveto(points[0].x, points[0].y)
        return path
    if len(points) == 2:
        path = BezierPath(None)
        path.moveto(points[0].x, points[0].y)
        path.lineto(points[1].x, points[1].y)
        return path
              
    # Zero curvature means straight lines.
    
    curvature = max(0, min(1, curvature))
    if curvature == 0:
        path = BezierPath(None)
        path.moveto(points[0].x, points[0].y)
        for i in range(len(points)): 
            path.lineto(points[i].x, points[i].y)
        return path
        
    curvature = 4 + (1.0-curvature)*40
    
    dx = {0: 0, len(points)-1: 0}
    dy = {0: 0, len(points)-1: 0}
    bi = {1: -0.25}
    ax = {1: (points[2].x-points[0].x-dx[0]) / 4}
    ay = {1: (points[2].y-points[0].y-dy[0]) / 4}
    
    for i in range(2, len(points)-1):
        bi[i] = -1 / (curvature + bi[i-1])
        ax[i] = -(points[i+1].x-points[i-1].x-ax[i-1]) * bi[i]
        ay[i] = -(points[i+1].y-points[i-1].y-ay[i-1]) * bi[i]
        
    r = range(1, len(points)-1)
    r.reverse()
    for i in r:
        dx[i] = ax[i] + dx[i+1] * bi[i]
        dy[i] = ay[i] + dy[i+1] * bi[i]

    path = BezierPath(None)
    path.moveto(points[0].x, points[0].y)
    for i in range(len(points)-1):
        path.curveto(points[i].x + dx[i], 
                     points[i].y + dy[i],
                     points[i+1].x - dx[i+1], 
                     points[i+1].y - dy[i+1],
                     points[i+1].x,
                     points[i+1].y)
    
    return path

def insert_point(path, t):
    
    """Returns a path copy with an extra point at t.
    >>> path = BezierPath(None)
    >>> path.moveto(0, 0)
    >>> insert_point(path, 0.1)
    Traceback (most recent call last):
        ...
    NodeBoxError: The given path is empty
    >>> path.moveto(0, 0)
    >>> insert_point(path, 0.2)
    Traceback (most recent call last):
        ...
    NodeBoxError: The given path is empty
    >>> path.lineto(100, 50)
    >>> len(path)
    2
    >>> path = insert_point(path, 0.5)
    >>> len(path)
    3
    >>> path[1]
    PathElement(LINETO, ((50.0, 25.0),))
    >>> path = BezierPath(None)
    >>> path.moveto(0, 100)
    >>> path.curveto(0, 50, 100, 50, 100, 100)
    >>> path = insert_point(path, 0.5)
    >>> path[1]
    PathElement(LINETO, ((25.0, 62.5), (0.0, 75.0), (50.0, 62.5))
    """
    
    i, t, closeto = _locate(path, t)
    
    x0 = path[i].x
    y0 = path[i].y
    p1 = path[i+1]
    p1cmd, x3, y3, x1, y1, x2, y2 = p1.cmd, p1.x, p1.y, p1.ctrl1.x, p1.ctrl1.y, p1.ctrl2.x, p1.ctrl2.y
    
    if p1cmd == CLOSE:
        pt_cmd = LINETO
        pt_x, pt_y = linepoint(t, x0, y0, closeto.x, closeto.y)
    elif p1cmd == LINETO:
        pt_cmd = LINETO
        pt_x, pt_y = linepoint(t, x0, y0, x3, y3)
    elif p1cmd == CURVETO:
        pt_cmd = CURVETO
        pt_x, pt_y, pt_c1x, pt_c1y, pt_c2x, pt_c2y, pt_h1x, pt_h1y, pt_h2x, pt_h2y = \
            curvepoint(t, x0, y0, x1, y1, x2, y2, x3, y3, True)
    else:
        raise NodeBoxError, "Locate should not return a MOVETO"
    
    new_path = BezierPath(None)
    new_path.moveto(path[0].x, path[0].y)
    for j in range(1, len(path)):
        if j == i+1:
            if pt_cmd == CURVETO:
                new_path.curveto(pt_h1x, pt_h1y,
                             pt_c1x, pt_c1y,
                             pt_x, pt_y)
                new_path.curveto(pt_c2x, pt_c2y,
                             pt_h2x, pt_h2y,
                             path[j].x, path[j].y)
            elif pt_cmd == LINETO:
                new_path.lineto(pt_x, pt_y)
                if path[j].cmd != CLOSE:
                    new_path.lineto(path[j].x, path[j].y)
                else:
                    new_path.closepath()
            else:
                raise NodeBoxError, "Didn't expect pt_cmd %s here" % pt_cmd
            
        else:
            if path[j].cmd == MOVETO:
                new_path.moveto(path[j].x, path[j].y)
            if path[j].cmd == LINETO:
                new_path.lineto(path[j].x, path[j].y)
            if path[j].cmd == CURVETO:
                new_path.curveto(path[j].ctrl1.x, path[j].ctrl1.y,
                             path[j].ctrl2.x, path[j].ctrl2.y,
                             path[j].x, path[j].y)
            if path[j].cmd == CLOSE:
                new_path.closepath()
    return new_path
    
def _test():
    import doctest, bezier
    return doctest.testmod(bezier)

if __name__=='__main__':
    _test()
