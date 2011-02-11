# by mark meyer | http://www.photo-mark.com | enjoy. 

size(600, 800)
strokewidth(1)
stroke(.45, .45, .25, .35)
nofill()
 
translate(300, 800) #starting point
 
segmentLength = 3
rightTurnAngle = 25.7
leftTurnAngle =  -25.7
 
rules= {}
# The symbols for the formal language are: 
# [ = save state (i.e push()).  ] = restore state (i.e. pop()). 
# + and - = turn right and left respectively (based on angles given above)
# Other symbolds are recursively substituted 
# and then processed as a draw forward instruction
rules['w'] = 'X' # This is the starting rule
rules['X'] = 'F[+X][-X]FX'
rules['F'] = 'FF'
 
# Be careful with large numbers of iterations,
# the complexity grows exponentially
iterations = 8
 
def draw():
    beginpath(0, 0)
    lineto(0, -segmentLength)
    endpath()
    transform(mode=CORNER)
    translate(0, -segmentLength)
    
def iterate(n, rule):
    if rule == '+':
        rotate(rightTurnAngle)
        return
    elif rule == '-':
        rotate(leftTurnAngle)
        return
    elif rule == "[": 
        push()
        return
    elif rule == "]":
         pop()
         return
    if n > 0:
        #scale(.98) # scaling on each iteration is fun to play with
        for step in rules[rule]:
            iterate(n-1, step)
    else: draw()
 
iterate(iterations, 'w')

