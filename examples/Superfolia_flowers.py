# flowers by Tom de Smedt

size(500, 500)
supershape = ximport("supershape")
def flower(x, y, r):
 
    em = 10
    n1 = 1.35
    n2 = -0.8 + random(-0.2)
    n3 = 0.4
    points = 400
    
    w = h = r
    p = supershape.path(x+20, y+20, w, h, em, n1, n2, n3, points)
    fill(0,0,0, 0.5)
    nostroke()
    drawpath(p)
    
    n = 20
    w = h = r + n
    for i in range(n):
        p = supershape.path(x, y, w, h, em, n1, n2, n3, points)
        w -= 4
        h -= 4
        d = float(i)/n
        fill(1, d, d+0.25, 0.1)
        stroke(1,0,0.2)
        strokewidth(0.25)
        drawpath(p)
        
nofill()
stroke(0)
x, y = 259, 434
 
for i in range(20):
    rotate(random(360))
    flower(200+random(200), 200+random(200), random(10,100-i*4))

