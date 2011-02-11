size(500, 500)

stroke(0,0,0)
nofill()

points = [ 
    (100, 100),
    (200, 200),
    (350, 200)]

for x, y in points:
    oval(x-2, y-2, 4, 4)

autoclosepath(False)
path = findpath(points)
drawpath(path)

