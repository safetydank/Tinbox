autoclosepath(False)
nofill()

beginpath(100, 500)
curveto(200,250, 600,600, 400,300)
path = endpath(draw=False)

stroke(0.5)
path.addpoint(0.25)
drawpath(path)
stroke(0.2)
for point in path:
    oval(point.x-4, point.y-4, 8, 8)


