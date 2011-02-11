# setup canvas
size(600, 600)
colormode(RGB)

# set background and foreground colors
background(0.3, 0.3, 1, 0.75)

# draw a rectangle
fill(0.4,0.1,0.1,0.2)
rect(10, 10, 100, 100, roundness=0.3)

# draw a line
stroke(1,1,0)
line(200, 200, 300, 300)

stroke(None)
oval(300, 300, 200, 150)

fill(None)
stroke(1, 0, 0)
oval(20, 300, 200, 150)

