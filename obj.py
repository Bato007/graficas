from os import execlp
import struct

def color(r, g, b):
    return bytes([b, g, r])

class Obj(object):
    def __init__(self, filename):
        with open(filename) as f:
            self.lines = f.read().splitlines()

        self.vertices = []
        self.tvertices = []
        self.normal = []
        self.faces = []
        self.read()

    def read(self):
        for line in  self.lines:
            try:
                if line:
                    prefix, value = line.split(' ', 1)

                    # Se separan
                    if prefix == 'v':
                        self.vertices.append(
                            list(map(float, value.split(' ')))
                        )
                    elif prefix == 'vt':
                        self.tvertices.append(
                            list(map(float, value.split(' ')))
                        )
                    elif prefix == 'vn':
                        self.normal.append(
                            list(map(float, value.split(' ')))
                        )
                    elif prefix == 'f':
                        self.faces.append(
                            [list(map(int, face.split('/'))) for face in value.split(' ')]
                        )
            except:
                pass

class Texture(object):
    def __init__(self, path):
        self.path = path
        self.pixels = []
        self.read()
    
    def read(self):
        image = open(self.path, 'br')
        image.seek(10)
        header_size = struct.unpack('=l', image.read(4))[0]

        image.seek(18)
        # Obteniendo el largo de la iamgen
        self.width = struct.unpack('=l', image.read(4))[0]
        self.height = struct.unpack('=l', image.read(4))[0]

        image.seek(header_size)

        # Llenando la imagen
        for _ in range(self.height):
            temp = []
            for _ in range(self.width):
                b = ord(image.read(1))
                g = ord(image.read(1))
                r = ord(image.read(1))
                temp.append(color(r, g, b))
            self.pixels.append(temp)
        image.close()

    def get_color(self, tx, ty):
        x = int(tx * self.width)
        y = int(ty * self.height)

        return self.pixels[y][x]
