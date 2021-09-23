class Matrix(object):
    # Las matrices se leen m x n
    def __init__(self, matrix):
        self.matrix = matrix
        self.m = len(matrix)
        self.n = len(matrix[0]) if self.m > 0 else 0
    
    def __repr__(self):
        if (self.m == 0):
            return '[]'

        matrix = ''
        for m in range(self.m):
            matrix += '[ '
            for n in range(self.n):
                matrix += (str(self.matrix[m][n]) + ' ')
            matrix += ']\n'
        return matrix

    def __add__(self, o):
        if (self.n != o.n) or (self.m != o.m):
            return None
        
        result = []
        # Se restan las coordenadas
        for m in range(self.m):
            result.append([])
            for n in range(self.n):
                result[m].append(self.matrix[m][n] + o.matrix[m][n])
        return Matrix(result)
    
    def __sub__(self, o):
        if (self.n != o.n) or (self.m != o.m):
            return None
        
        result = []
        # Se restan las coordenadas
        for m in range(self.m):
            result.append([])
            for n in range(self.n):
                result[m].append(self.matrix[m][n] - o.matrix[m][n])
        return Matrix(result)

    def __mul__(self, o):
        if (self.n != o.m):
            return None
        
        result = []
        for _ in range(self.m):    # Estableciendo filas
            result.append([])

        # Obteniendo los multiplicadores
        mult = []
        for on in range(o.n):
            mult.append([])
            for om in range(o.m):
                mult[on].append(o.matrix[om][on])

        # Realizando la multiplicacion
        j = 0
        for mm in range(len(mult)): # Selecciono el vector a mult
            for sm in range(self.m): # Selecciono la fila
                temp = 0
                for i in range(self.n): # Elementos de cada fila
                    temp += self.matrix[sm][i] * mult[mm][i]
                result[j].append(temp)
                j = (j + 1) % (self.m) 

        return Matrix(result)
