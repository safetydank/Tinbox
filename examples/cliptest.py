size(100,100)

fill(1,1,0)
path = oval(10, 10, 40, 40, draw=False)
beginclip(path)
rect(0, 0, 30, 30)
endclip()

fill(0.2, 0.5, 0.2, 0.1)
rect(0, 0, 50, 50, roundness=0.15)

