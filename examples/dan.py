# loosely based on the cover of the Processing book

from math import pi, sin, cos

size(800, 800)
background(1, 1, 1)

n = 150
nostroke()

def radial_gradient(colors, x, y, radius, steps=300):
 
    """ Radial gradient using the given list of colors.
    """
 
    def _step(colors, i, n):
        l = len(colors)-1
        a = int(1.0*i/n*l)
        a = min(a+0, l)
        b = min(a+1, l)
        base = 1.0 * n/l * a
        d = (i-base) / (n/l)
        r = colors[a].r*(1-d) + colors[b].r*d
        g = colors[a].g*(1-d) + colors[b].g*d
        b = colors[a].b*(1-d) + colors[b].b*d
        return color(r, g, b)
 
    for i in range(steps):
        fill(_step(colors, i, steps))
        oval(x+i, y+i, radius-i*2, radius-i*2)  
 
def cell(x, y, size, a=0.04):
    fill(0.2, 0.2, 0.6, 0.17)
    oval(x - size/2, y - size/2, size, size)
    fill(0.34, 0.34, 0.6, 0.04)
    edge = 5
    oval(x - size/2 + edge, y - size/2 + edge, size - 2*edge, size - 2*edge)
    # shadow
    fill(0.2, 0.01)
    oval(x - size/2 + 16, y - size/2 + 16, size, size)

clusters = 10

points = []
sets   = []

radial_gradient(
    [color(0.3, 0.3, 0.4), color(0.9, 0.9, 1.0)],
    -400, -400,
    radius=1500
) 

for g in range(clusters):
    (ox, oy) = (random(100, 700), random(100,700))
    for i in range(n/clusters):
        m, t = random(20, 400), random(0, 2*pi)
        x, y = ox + m * cos(t), oy + m * sin(t)
        if (x < 200 or x > 600) and (y < 200 or y > 600):
            continue

        size = random(50, 120)
        cell(x, y, size)
        points.append(((x, y), (ox, oy)))

for i in range(11):
    (ox, oy) = (random(0, 200), random(0,200))
    if ox > 100: ox += 600
    if oy > 100: oy += 600

    m, t = random(0, 400), random(0, 2*pi)
    x, y = ox + m * cos(t), oy + m * sin(t)

    size = random(400, 600)
    cell(x, y, size, 0.01)
    points.append(((x, y), (ox, oy)))
    

drawn = {}
for i in range(20):
    ((x1, y1), (cx1, cy1)), ((x2, y2), (cx2, cy2)) = choice(points), choice(points)

    for (x,y) in ((x1, y1), (x2, y2)):
        if not drawn.get((x, y)):
            drawn[(x, y)] = 0
        else:
            drawn[(x, y)] += 1 

    nofill()
    stroke(0, 0.2)
    strokewidth(0.5)
    if (drawn[(x1,y1)] < 1 and drawn[(x2, y2)] < 1):
        beginpath(x1, y1)
        curveto(cx1, cy1, cx2, cy2, x2, y2)
        endpath()
    
    nostroke()
    fill(0.2, 0.5)
    oval(x1-2, y1-2, 4, 4)
    oval(x2-2, y2-2, 4, 4)
    

