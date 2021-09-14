import struct
from obj import Obj, Texture
import aritmetic as ar
from aritmetic import V3, Square, Triangle


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
        self.current_color = WHITE
        self.clear_color = BLACK
        self.clear()

        # Para los puertos
        self.port_width = width
        self.port_height = height
        self.x = 0
        self.y = 0

        self.xm = round(width/2)
        self.ym = round(height/2)

        # Para modelos
        self.msquares = []
        self.mtriangles = []

        # Para texturas
        self.texture = None
        self.tsquares = []
        self.ttriangles = []

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


    def load_texture(self, filename):
        self.texture = Texture(filename)


    def load3d(self, filename, traslation=(0, 0, 0), scale=(1, 1, 1)):
        model = Obj(filename)

        for face in model.faces:
            size = len(face)

            vertices = []
            tvertices = []
            for i in range(size):  # Se obtienen los vertices
                fi = face[i][0] - 1
                point = model.vertices[fi]

                # Ahora se convirte normalizados a screen
                xf = round((point[0] + traslation[0]) * scale[0])
                yf = round((point[1] + traslation[1]) * scale[1])
                zf = round((point[2] + traslation[2]) *scale[2])

                # Ahora se convierte en V3 y se mete
                P = V3(xf, yf, zf)
                vertices.append(P)

                # ----TEXTURAS----
                tf = face[i][1] - 1
                tpoint = model.tvertices[tf]
                tx = tpoint[0]
                ty = tpoint[1]          

                # Ahora se convierte en V3 y se mete
                tP = V3(tx, ty)
                tvertices.append(tP)

            if size == 4:
                self.msquares.append(Square(*vertices))
                self.tsquares.append(Square(*tvertices))
            elif size == 3:
                self.mtriangles.append(Triangle(*vertices))
                self.ttriangles.append(Triangle(*tvertices))


def glCreateWindow(width, height):
    global frame
    frame = Renderer(width, height)


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


def paintTriangle(A, B, C, texture_coords=None, paint=None):
    xmin, xmax, ymin, ymax = ar.minbox(A, B, C)

    # Se pinta el triangulo
    for x in range(xmin, xmax + 1):
        for y in range(ymin, ymax + 1):
            P = V3(x, y)
            w, v, u = ar.barycentric(A, B, C, P)

            if w < 0 or v < 0 or u < 0:
                continue
            
            # Esta dentro del triangulo
            normal = ar.getNormalDirection(A, B, C)

            # Luego la intensidad con la que se pinta
            intensity = ar.pointProduct(normal, frame.light)

            base = round(200 * intensity)

            if (base < 0):
                continue
            elif (base > 255):
                base = 255

            # Aqui se decide como se va a pintar
            if frame.texture:
                tA, tB, tC = texture_coords
                tx = tA.x * w + tB.x * v + tC.x * u
                ty = tA.y * w + tB.y * v + tC.y * u
                tcolor = frame.texture.get_color(tx, ty)
                b, g, r = [int(c * intensity) if intensity > 0 else 0 for c in tcolor]
                paint_color = color(r, g, b)
            else:
                paint_color = paint or color(base, base, base)

            z = (A.z * w) + (B.z * v) + (C.z * u)

            try:
                if z > frame.zbuffer[y][x]:
                    frame.do_point(x, y, paint_color)
                    frame.zbuffer[y][x] = z
            except:
                pass


def paintSquare(A, B, C, D, tA, tB, tC, tD):
    if frame.texture:
        paintTriangle(A, B, C, (tA, tB, tC))
        paintTriangle(A, C, D, (tA, tC, tD))
    else:
        paintTriangle(A, B, C)
        paintTriangle(A, C, D)


def glPaintModel(filename, traslation=(0, 0, 0), scale=(1, 1, 1), texturename=None):
    frame.load3d(filename, traslation, scale)
    if texturename:
        frame.load_texture(texturename)
    squares = frame.msquares
    triangles = frame.mtriangles
    tsquares = frame.tsquares
    ttriangles = frame.ttriangles

    # Se pintan los cuadrados
    for i in range(len(squares)):
        A, B, C, D = squares[i].getVertices()
        tA, tB, tC, tD = tsquares[i].getVertices()
        paintSquare(A, B, C, D, tA, tB, tC, tD)
    # Se pintan los triangulos
    for i in range(len(triangles)):
        A, B, C = triangles[i].getVertices()
        tA, tB, tC = ttriangles[i].getVertices()
        if frame.texture: # Se le pasa la textura
            paintTriangle(A, B, C, (tA, tB, tC))
        else: 
            paintTriangle(A, B, C)


glCreateWindow(800, 600)
glPaintModel('./models/earth.obj', (800, 600, 0), (0.5, 0.5, 1), './models/earth.bmp')
# glPaintModel('./models/model.obj', (1, 1, 0), (300, 300, 300), './models/model.bmp')
glFinish('out')
