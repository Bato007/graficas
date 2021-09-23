import struct, random
from math import sin, cos
from obj import Obj, Texture
import vector as ar
from vector import V3, Triangle
from matrix import Matrix


def char(c):
    # ocupa 1 byte
    return struct.pack('=c', c.encode('ascii'))


def word(w):
    # short, ocupa 2 bytes
    return struct.pack('=h', w)


def dword(dw):
    # long, ocupa 4 bytes
    return struct.pack('=l', dw)


def color(r, g, b):
    return bytes([b, g, r])


BLACK = color(0, 0, 0)
WHITE = color(255, 255, 255)


class Renderer(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.widthm = width/2
        self.heightm = height/2
        self.current_color = WHITE
        self.clear_color = BLACK
        self.clear()

        # Para modelos
        self.mtriangles = []

        # Para texturas
        self.texture = None
        self.currentt = None
        self.ttriangles = []

        # Para normales
        self.currentn = None
        self.normals = []

        # Shaders
        self.activeShader = None
        self.hasnormalmap = False
        self.normalmap = None

        # Modelos en 3d
        self.light = V3(0, 0, 1)


    def clear(self):
        self.buffer = [
            [self.clear_color for _ in range(self.width)]
            for _ in range(self.height)
        ]

        self.zbuffer = [
            [-99999 for _ in range(self.width)]
            for _ in range(self.height)
        ]


    def write(self, filename):
        f = open(filename, 'bw')
        # file header ' siempre es BM y ocupa 14 bytes
        f.write(char('B'))
        f.write(char('M'))
        # Se multiplica por tres por ser rgb
        f.write(dword(14 + 40 + 3*(self.width*self.height)))
        f.write(dword(0))
        f.write(dword(14+40))  # En donde

        # info header '
        f.write(dword(40))  # Tamaño del info header
        f.write(dword(self.width))
        f.write(dword(self.height))
        f.write(word(1))    # pela pero se pone
        f.write(word(24))   # Siempre es 24
        f.write(dword(0))   # pela
        f.write(dword(3*(self.width*self.height)))

        for _ in range(4):        # Cosas que pelan
            f.write(dword(0))

        # bitmap
        for y in range(self.height):
            for x in range(self.width):
                f.write(self.buffer[y][x])

        f.close()


    def do_point(self, x, y, color=None):
        self.buffer[y][x] = color or self.current_color

    
    def loadModelMatrix(self, traslate=(0, 0, 0), scale=(1, 1, 1), rotate=(0, 0, 0)):
        # Para mover el modelo
        traslation_matrix = Matrix([
            [1, 0, 0, traslate[0]],
            [0, 1, 0, traslate[1]],
            [0, 0, 1, traslate[2]],
            [0, 0, 0, 1]
        ])

        # Para rotar el modelo
        a = rotate[0]
        rotationmx = Matrix([
            [1, 0, 0, 0],
            [0, cos(a), -sin(a), 0],
            [0, sin(a), cos(a), 0],
            [0, 0, 0, 1]
        ])

        a = rotate[1]
        rotationmy = Matrix([
            [cos(a), 0, sin(a), 0],
            [0, 1, 0, 0],
            [-sin(a), 0, cos(a), 0],
            [0, 0, 0, 1]
        ])

        a = rotate[2]
        rotationmz = Matrix([
            [cos(a), -sin(a), 0, 0],
            [sin(a), cos(a), 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])

        rotation_matrix = rotationmx * rotationmy * rotationmz

        # La escala se modifica
        scale_matrix = Matrix([
            [scale[0], 0, 0, 0],
            [0, scale[1], 0, 0],
            [0, 0, scale[2], 0],
            [0, 0, 0, 1]
        ])


        self.Model = traslation_matrix * rotation_matrix * scale_matrix


    def loadViewMatrix(self, x, y, z, center):
        M = Matrix([
            [x.x, x.y, x.z, 0],
            [y.x, y.y, y.z, 0],
            [z.x, z.y, z.z, 0],
            [0, 0, 0, 1]
        ])

        O = Matrix([
            [1, 0, 0, -center.x],
            [0, 1, 0, -center.y],
            [0, 0, 1, -center.z],
            [0, 0, 0, 1]
        ])

        self.View = M * O


    def loadProjectionMatrix(self, coeff):
        self.Projection = Matrix([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, coeff, 1]
        ])


    def loadViewPortMatrix(self, x=0, y=0):
        self.ViewPort = Matrix([
            [self.widthm, 0, 0, x + self.widthm],
            [0, self.heightm, 0, y + self.heightm],
            [0, 0, 128, 128],
            [0, 0, 0, 1]
        ])


    def lookAt(self, eye, center, up):
        z = ar.getDirection(ar.subVector(eye, center))
        x = ar.getDirection(V3(*ar.crossProduct(up, z)))
        y = ar.getDirection(V3(*ar.crossProduct(z, x)))
        
        self.loadViewMatrix(x, y, z, center)
        self.loadProjectionMatrix(
            -1/ar.vectorLen(ar.subVector(eye, center))
        )
        self.loadViewPortMatrix(0, 0)


    def transform(self, vector):
        temp = Matrix([
            [vector.x],
            [vector.y],
            [vector.z],
            [1]
        ])
        # Se realizan las transformaciones
        transformed = self.Matrix * temp 
        result = transformed.matrix
        x = round(result[0][0]/result[3][0])
        y = round(result[1][0]/result[3][0])
        z = round(result[2][0]/result[3][0])
        return V3(x, y, z)


    def load_texture(self, filename):
        self.texture = Texture(filename)
    

    def load_normal(self, filename):
        self.normalmap = Texture(filename)
        self.hasnormalmap = True


    def load3d(self, filename, traslate=(0, 0, 0), scale=(1, 1, 1), rotate=(0, 0, 0)):
        model = Obj(filename)
        self.loadModelMatrix(traslate, scale, rotate)
        self.Matrix = self.ViewPort * self.Projection * self.View * self.Model
        normall = len(model.normal) > 0

        for face in model.faces:
            size = len(face)

            vertices = []
            tvertices = []
            normale = []
            for i in range(size):  # Se obtienen los vertices
                fi = face[i][0] - 1
                point = model.vertices[fi]

                # Ahora se convierte en V3 y se mete
                P = V3(*point)
                P = self.transform(P)
                vertices.append(P)

                # ----TEXTURAS----
                tf = face[i][1] - 1
                tpoint = model.tvertices[tf]       

                # Ahora se convierte en V3 y se mete
                tP = V3(*tpoint)
                tvertices.append(tP)

                # ---NORMALES---
                if normall:
                    tn = face[i][2] - 1
                    normal = model.normal[tn]      

                    # Ahora se convierte en V3 y se mete
                    nP = V3(*normal)
                    normale.append(nP)

            if size == 4:
                A, B, C, D = vertices
                tA, tB, tC, tD = tvertices
                self.mtriangles.append(Triangle(A, B, C))
                self.mtriangles.append(Triangle(A, C, D))
                self.ttriangles.append(Triangle(tA, tB, tC))
                self.ttriangles.append(Triangle(tA, tC, tD))
                if normall:
                    nA, nB, nC, nD = normale
                    self.normals.append(Triangle(nA, nB, nC))
                    self.normals.append(Triangle(nA, nC, nD))
            elif size == 3:
                self.mtriangles.append(Triangle(*vertices))
                self.ttriangles.append(Triangle(*tvertices))
                if normall:
                    self.normals.append(Triangle(*normale))


def aux(A, B, C):
    normal = ar.getNormalDirection(A, B, C)

    # Luego la intensidad con la que se pinta
    return ar.pointProduct(normal, frame.light)


def shader(**kwargs):
    w, v, u = kwargs['bar']
    tx, ty = kwargs['tcords']
    nA, nB, nC = kwargs['normals']

    tcolor = frame.texture.get_color(tx, ty)
    iA, iB, iC = [ar.pointProduct(n, frame.light) for n in (nA, nB, nC)]
    intensity = w*iA + v*iB + u*iC
    b, g, r = [int(c * intensity) if intensity > 0 else 0 for c in tcolor]

    return color(r, g, b)


def mapshader(**kwargs):
    tx, ty = kwargs['tcords']

    tcolor = frame.texture.get_color(tx, ty)
    ncolor = frame.normalmap.get_color(tx, ty)
    z, y, x = [int(c)/255 for c in (ncolor)]
    ncolor = V3(x, y, z)
    intensity = ar.pointProduct(ncolor, frame.light)
    
    b, g, r = [int(c * intensity) if intensity > 0 else 0 for c in tcolor]
    return color(r, g, b)


def fragment(**kwargs):
    w, v, u = kwargs['bar']
    tx, ty = kwargs['tcords']
    nA, nB, nC = kwargs['normals']

    grey = int(ty * 256)
    tcolor = color(grey, 100, 100)

    iA, iB, iC = [ar.pointProduct(n, frame.light) for n in (nA, nB, nC)]
    intensity = w*iA + v*iB + u*iC

    if intensity > 0.85:
        intensity = 1
    elif intensity > 0.60:
        intensity = 0.80
    elif intensity > 0.45:
        intensity = 0.60
    elif intensity > 0.30:
        intensity = 0.45
    elif intensity > 0.15:
        intensity = 0.30
    else:
        intensity = 0

    b, g, r = [int(c * intensity) if intensity > 0 else 0 for c in tcolor]

    return color(r, g, b)


def grass(**kwargs):
    w, v, u = kwargs['bar']
    tx, ty = kwargs['tcords']
    nA, nB, nC = kwargs['normals']

    iA, iB, iC = [ar.pointProduct(n, frame.light) for n in (nA, nB, nC)]
    intensity = w*iA + v*iB + u*iC

    if ty > 0.5 or ty < 0:
        tcolor = color(25, 25, 112) if random.randint(0, 1000) < 999 else color(255, 205, 60)
    else:
        tcolor = color(0, 154, 23) if random.randint(0, 1000) < 990 else color(155, 118, 83)

    b, g, r = [int(c * intensity) if intensity > 0 else 0 for c in tcolor]

    return color(r, g, b)


def star(**kwargs):
    w, v, u = kwargs['bar']
    tx, ty = kwargs['tcords']
    nA, nB, nC = kwargs['normals']

    iA, iB, iC = [ar.pointProduct(n, frame.light) for n in (nA, nB, nC)]
    intensity = (w*iA + v*iB + u*iC)*tx*ty

    tcolor = color(200, 200, 200)

    b, g, r = [int(c * intensity) if intensity > 0 else 0 for c in tcolor]

    return color(r, g, b)

def normalShader(tx, ty, intensity):
    tcolor = frame.texture.get_color(tx, ty)
    b, g, r = [int(c * intensity) if intensity > 0 else 0 for c in tcolor]
    return color(r, g, b)


def glCreateWindow(width, height):
    global frame
    frame = Renderer(width, height)
    frame.activeShader = shader


def line(A, B):
    x0, y0 = A.x, A.y
    x1, y1 = B.x, B.y
    dy = y1 - y0
    dx = x1 - x0

    desc = (dy*dx) < 0

    dy = abs(dy)
    dx = abs(dx)

    steep = dy > dx

    if steep:
        x0, y0 = y0, x0
        x1, y1 = y1, x1

        dy = abs(y1 - y0)
        dx = abs(x1 - x0)

    if desc and (y0 < y1):
        y0, y1 = y1, y0
    elif (not desc) and (y1 < y0):
        y0, y1 = y1, y0

    if (x1 < x0):
        x1, x0 = x0, x1

    offset = 0
    threshold = dx
    y = y0

    # y = mx + b
    points = []
    for x in range(x0, x1+1):
        if steep:
            points.append((y, x))
        else:
            points.append((x, y))

        offset += dy * 2
        if offset >= threshold:
            y += 1 if y0 < y1 else -1
            threshold += 1 * 2 * dx
    
    for point in points:
        frame.do_point(*point)


def glFinish(name):
    frame.write(str(name) + '.bmp')


def paintTriangle(A, B, C):
    has_normals = len(frame.normals) > 0
    xmin, xmax, ymin, ymax = ar.minbox(A, B, C)
    pdabc = ar.promDistance(A, B, C) if frame.activeShader == grass else None
    if has_normals:
        nA, nB, nC = frame.currentn

    # Se pinta el triangulo
    for x in range(xmin, xmax + 1):
        for y in range(ymin, ymax + 1):
            w, v, u = ar.barycentric(A, B, C, V3(x, y))

            if w < 0 or v < 0 or u < 0:
                continue
            
            # Aqui se decide como se va a pintar
            if frame.currentt:
                tA, tB, tC = frame.currentt
                tx = (tA.x * w + tB.x * v + tC.x * u)
                ty = (tA.y * w + tB.y * v + tC.y * u)

                if has_normals:
                    paint_color = frame.activeShader(
                        bar=(w, v, u),
                        tcords=(tx, ty),
                        normals=(nA, nB, nC)
                    )
                
                else:
                    intensity = aux(A, B, C)
                    paint_color = normalShader(tx, ty, intensity)

            else:

                if has_normals:
                    tx = ((A.x * w) + (B.x * v) + (C.x * u))/frame.width
                    ty = ((A.y * w) + (B.y * v) + (C.y * u))/frame.height

                    paint_color = frame.activeShader(
                        distance=(pdabc),
                        bar=(w, v, u),
                        tcords=(tx, ty),
                        normals=(nA, nB, nC)
                    )
                else:
                # Esta dentro del triangulo
                    intensity = aux(A, B, C)
                    base = round(200*intensity)

                    if (base < 0):
                        continue
                    elif (base > 255):
                        base = 255
                        
                    paint_color = color(base, base, base)

            z = (A.z * w) + (B.z * v) + (C.z * u)

            try:
                if z > frame.zbuffer[y][x]:
                    frame.do_point(x, y, paint_color)
                    frame.zbuffer[y][x] = z
            except:
                pass


def glPaintModel(
    filename, 
    traslation=(0, 0, 0), 
    scale=(1, 1, 1), 
    rotate=(0, 0, 0), 
    texturename=None,
    normalname=None
):
    frame.load3d(filename, traslation, scale, rotate)
    if texturename:
        frame.load_texture(texturename)
    if normalname:
        frame.load_normal(normalname)
    triangles = frame.mtriangles
    ttriangles = frame.ttriangles
    normales = frame.normals
    has_normal = len(normales) > 0

    # Se pintan los triangulos
    for i in range(len(triangles)):
        A, B, C = triangles[i].getVertices()
        tA, tB, tC = ttriangles[i].getVertices()
        if has_normal:
            nA, nB, nC = normales[i].getVertices()
        # Se le pasa la textura
        frame.currentt = (tA, tB, tC) if frame.texture else None
        frame.currentn = (nA, nB, nC) if has_normal else None
        paintTriangle(A, B, C)


def initCamera(eye, center, up):
    frame.lookAt(eye, center, up)


def activeShader(shader):
    frame.activeShader = shader


glCreateWindow(600, 600)
initCamera(V3(0, 0, 5), V3(0, 0, 0), V3(0, 1, 0))
pi = 3.14

activeShader(fragment)
glPaintModel(
    './project/sphere.obj', 
    (-1/2, 1/12, 1), 
    (1/16, 1/16, 1/2),
    (0, 0, 0))

activeShader(star)
glPaintModel(
    './project/star.obj', 
    (1/2, 1/2, 0), 
    (1/16, 1/16, 1/2),
    (0, 0, 0))

activeShader(grass)
glPaintModel(
    './project/block.obj', 
    (0, -1, 0), 
    (1, 2, 1/10),
    (0, 0, 0))

activeShader(shader)
glPaintModel(
    './project/free_head.obj', 
    (-1/2, -5, 0), 
    (2, 2, 1),
    (pi/8, 2*pi/3, 0),
    './models/model.bmp')

# activeShader(mapshader)
# glPaintModel(
#     './project/dog.obj', 
#     (0, 0, 1), 
#     (1/12, 1/12, 1/2),
#     (0, pi/8, 0),
#     './project/color.bmp',
#     './project/normal.bmp')

glFinish('out')
