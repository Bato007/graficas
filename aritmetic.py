class V3(object):
    def __init__(self, x, y, z=0):
        self.x = x
        self.y = y
        self.z = z


class Square(object):
    def __init__(self, A, B, C, D):
        self.A = A
        self.B = B
        self.C = C
        self.D = D

    def getVertices(self):
        return self.A, self.B, self.C, self.D


class Triangle(object):
    def __init__(self, A, B, C):
        self.A = A
        self.B = B
        self.C = C

    def getVertices(self):
        return self.A, self.B, self.C


def addVector(A, B):
    return V3(
        A.x + B.x,
        A.y + B.y,
        A.z + B.z
    )


def subVector(A, B):
    return V3(
        A.x - B.x,
        A.y - B.y,
        A.z - B.z
    )


def vectorLen(A):
    return (A.x**2 + A.y**2 + A.z**2)**0.5


def getDirection(A):
    length = vectorLen(A)

    if length == 0:
        return V3(0, 0, 0)

    return V3(
        A.x / length,
        A.y / length,
        A.z / length
    )
    

def crossProduct(A, B):
    cx = (A.y * B.z) - (A.z * B.y)
    cy = (A.z * B.x) - (A.x * B.z)
    cz = (A.x * B.y) - (A.y * B.x)
    return cx, cy, cz


def pointProduct(A, B):
    return ((A.x * B.x) + (A.y * B.y) + (A.z * B.z))


def barycentric(A, B, C, P):
    cx, cy, cz = crossProduct(
        V3(C.x - A.x, B.x - A.x, A.x - P.x),
        V3(C.y - A.y, B.y - A.y, A.y - P.y)
    )

    if cz == 0:
        return -1, -1, -1

    u = cx/cz
    v = cy/cz
    w = 1 - (u + v)

    return w, v, u


def getNormal(A, B, C):
    cx, cy, cz = crossProduct(
        subVector(B, A),
        subVector(C, A)
    )
    return V3(cx, cy, cz)


def getNormalDirection(A, B, C):
    return getDirection(getNormal(A, B, C))


def minbox(A, B, C):
    xs = [A.x, B.x, C.x]
    ys = [A.y, B.y, C.y]
    xs.sort()
    ys.sort()
    return xs[0], xs[-1], ys[0], ys[-1]
