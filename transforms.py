from gl import *
from math import sin, cos
from matrix import Matrix

glCreateWindow(1000, 1000)

points = Matrix([
    [200, 400, 400, 200],
    [200, 200, 400, 400],
    [1, 1, 1, 1]
])

# Rotaciones
a = 3.14/4
rotationm = Matrix([
    [cos(a), -sin(a), 0],
    [sin(a), cos(a), 0],
    [0,0,1]
])

moveorig = Matrix([
    [1, 0, -300],
    [0, 1, -300],
    [0, 0, 1]
])

transformi = Matrix([
    [1, 0, 0],
    [0, 1, 0],
    [0, 0.001, 1]
])

moveback = Matrix([
    [1, 0, 300],
    [0, 1, 300],
    [0, 0, 1]
])

final = (moveback * transformi * moveorig)
transformm = (final * points)

transformed = []
matri = transformm.matrix
for i in range(transformm.n):
    x = int(matri[0][i]/matri[2][i])
    y = int(matri[1][i]/matri[2][i])
    transformed.append([x, y])

print(transformed)
ppoint = V3(*transformed[-1])
for point in transformed:
    point = V3(*point)
    line(ppoint, point)
    ppoint = point

glFinish('out')
