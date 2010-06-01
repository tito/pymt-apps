cdef extern from "math.h":
    double sqrt(double)
    double cos(double)
    double sin(double)
    double floor(double)

cdef extern from "stdlib.h":
    int rand()

cdef int boundary(int v, int min, int max):
    if v < min:
        return min
    if v > max:
        return max
    return v
    

# VizScenarioTree
def drawTree(lines, double x, double y, double l, double d,
             double a, double z, double depth):
        cdef double f

        if depth >= 12:
            return

        f = 1 / (1 + float(depth) / 2.)
        dx = x + l * cos(d)
        dy = y + l * sin(d)
        lines.extend((x, y, dx, dy))
        l /= 1.4
        depth += 1

        drawTree(lines, dx, dy, l, d-a+z, a, z, depth)
        drawTree(lines, dx, dy, l, d+a+z, a, z, depth)

# VizScenarioPlasma
def plasmaUpdate(pos, cWaves, wave, wave2, pixels, luma, int w):
    cdef int ix, iy, iz, i, ip, ip2
    for ix in xrange(2):
        for iy in xrange(2):
            for iz in xrange(3):
                i = ix * 2 * 2 + iy * 2 + iz
                if ix + iy == 1:
                    pos[i] += 2 + int(rand() / 2147483647. * 2)
                    if pos[i] > 719:
                        pos[i] -= 720
                else:
                    pos[i] -= 2 + int(rand() / 2147483647. * 2)
                    if pos[i] < 0:
                        pos[i] += 720
    for ix in xrange(w):
        for iy in xrange(3):
            for iz in xrange(2):
                i = iz * 3 * w + iy * w + ix
                ip = (iz * 2 + iy)
                ip2 = (1 * 2 * 2 + iz * 2 + iy)
                cWaves[i] = wave[ix + pos[ip]] + wave2[ix + pos[ip2]]

    for ix in xrange(w):
        for iy in xrange(w):
            ip = iy * w * 3
            ip2 = ix * 3
            # I0 + I1 * w + I2 * w * 3
            pixels[ip + ip2] = \
                    luma[cWaves[ix] + cWaves[iy + w * 3]]
            pixels[ip + ip2 + 1] = \
                    luma[cWaves[ix + w] + cWaves[iy + w * 4]]
            pixels[ip + ip2 + 2] = \
                    luma[cWaves[ix + w * 2] + cWaves[iy + w * 5]]

# VizScenarioSmoke
p = (
151,160,137,91,90,15,131,13,201,95,96,53,194,233,7,225,140,36,103,
30,69,142,8,99,37,240,21,10,23,190,6,148,247,120,234,75,0,26,197,
62,94,252,219,203,117,35,11,32,57,177,33,88,237,149,56,87,174,20,
125,136,171,168,68,175,74,165,71,134,139,48,27,166,77,146,158,231,
83,111,229,122,60,211,133,230,220,105,92,41,55,46,245,40,244,102,
143,54,65,25,63,161,1,216,80,73,209,76,132,187,208,89,18,169,200,
196,135,130,116,188,159,86,164,100,109,198,173,186,3,64,52,217,226,
250,124,123,5,202,38,147,118,126,255,82,85,212,207,206,59,227,47,16,
58,17,182,189,28,42,223,183,170,213,119,248,152,2,44,154,163,70,
221,153,101,155,167,43,172,9,129,22,39,253,19,98,108,110,79,113,
224,232,178,185,112,104,218,246,97,228,251,34,242,193,238,210,144,
12,191,179,162,241,81,51,145,235,249,14,239,107,49,192,214,31,181,
199,106,157,184,84,204,176,115,121,50,45,127,4,150,254,138,236,
205,93,222,114,67,29,24,72,243,141,128,195,78,66,215,61,156,180,
151,160,137,91,90,15,131,13,201,95,96,53,194,233,7,225,140,36,103,
30,69,142,8,99,37,240,21,10,23,190,6,148,247,120,234,75,0,26,197,
62,94,252,219,203,117,35,11,32,57,177,33,88,237,149,56,87,174,20,
125,136,171,168,68,175,74,165,71,134,139,48,27,166,77,146,158,231,
83,111,229,122,60,211,133,230,220,105,92,41,55,46,245,40,244,102,
143,54,65,25,63,161,1,216,80,73,209,76,132,187,208,89,18,169,200,
196,135,130,116,188,159,86,164,100,109,198,173,186,3,64,52,217,226,
250,124,123,5,202,38,147,118,126,255,82,85,212,207,206,59,227,47,16,
58,17,182,189,28,42,223,183,170,213,119,248,152,2,44,154,163,70,
221,153,101,155,167,43,172,9,129,22,39,253,19,98,108,110,79,113,
224,232,178,185,112,104,218,246,97,228,251,34,242,193,238,210,144,
12,191,179,162,241,81,51,145,235,249,14,239,107,49,192,214,31,181,
199,106,157,184,84,204,176,115,121,50,45,127,4,150,254,138,236,
205,93,222,114,67,29,24,72,243,141,128,195,78,66,215,61,156,180)

def lerp(double t, double a, double b):
    return a + t * (b - a)

def fade(double t):
    return t * t * t * (t * (t * 6 - 15) + 10)

def grad(int hash, double x, double y, double z):
    h = hash & 15
    if h < 8:
        u = x
    else:
        u = y
    if h < 4:
        v = y
    elif h == 12 or h == 14:
        v = x
    else:
        v = z
    if h & 1 != 0:
        u = -u
    if h & 2 != 0:
        v = -v
    return u + v

def noise(double x, double y, double z):
    cdef int X, Y, Z, A, AA, AB, B, BA, BB
    cdef double u, v, w
    cdef int pAA, pAB, pBA, pBB, pAA1, pBA1, pAB1, pBB1,
    cdef double gradAA, gradBA, gradAB, gradBB
    cdef double gradAA1, gradBA1, gradAB1, gradBB1

    global p

    X = int(floor(x)) & 255
    Y = int(floor(y)) & 255
    Z = int(floor(z)) & 255
    x -= floor(x)
    y -= floor(y)
    z -= floor(z)

    u = fade(x)
    v = fade(y)
    w = fade(z)

    A =  p[X] + Y
    AA = p[A] + Z
    AB = p[A + 1] + Z
    B =  p[X + 1] + Y
    BA = p[B] + Z
    BB = p[B + 1] + Z

    pAA = p[AA]
    pAB = p[AB]
    pBA = p[BA]
    pBB = p[BB]
    pAA1 = p[AA + 1]
    pBA1 = p[BA + 1]
    pAB1 = p[AB + 1]
    pBB1 = p[BB + 1]

    gradAA =  grad(pAA, x,   y,   z)
    gradBA =  grad(pBA, x-1, y,   z)
    gradAB =  grad(pAB, x,   y-1, z)
    gradBB =  grad(pBB, x-1, y-1, z)
    gradAA1 = grad(pAA1,x,   y,   z-1)
    gradBA1 = grad(pBA1,x-1, y,   z-1)
    gradAB1 = grad(pAB1,x,   y-1, z-1)
    gradBB1 = grad(pBB1,x-1, y-1, z-1)
    return lerp(w,
        lerp(v, lerp(u, gradAA, gradBA), lerp(u, gradAB, gradBB)),
        lerp(v, lerp(u, gradAA1,gradBA1),lerp(u, gradAB1,gradBB1)))

def smokeUpdate(int w, p, double z, double z2, double wf, double t):
    cdef double X, Y
    cdef int cl, x
    for x in xrange(w * w):
        X = ((x % w) / wf) * z - z2
        Y = ((x / w) / wf) * z - z2
        cl = max(0, min(255, int((noise(X, Y, t) - .3) * 512)))
        p[x*3] = cl
        p[x*3+1] = cl
        p[x*3+2] = min(255, cl * 2)


def waterWave(int w, int h, list waves, int currentWave, int previousWave,
              double damping):
    cdef int x, y
    for y in xrange(1, h-1):
        for x in xrange(1, w-1):
            waves[currentWave][x][y] = <int>((( 
                waves[previousWave][x-1][y] + 
                waves[previousWave][x+1][y] +
                waves[previousWave][x][y-1] +
                waves[previousWave][x][y+1] ) / 2 -
                    waves[currentWave][x][y]) * damping)


def waterDraw(int w, int h, list waves, int currentWave,
              list r, list g, list b, render):
    cdef int x, y, Xoffset, Yoffset, xnew, ynew, shading, idx
    cdef int pr, pg, pb
    for y in xrange(1,h -1):
        for x in xrange(1,w -1):
            
            Xoffset = <int>(waves[currentWave][x-1][y] - waves[currentWave][x+1][y])/40
            Yoffset = <int>(waves[currentWave][x][y-1] - waves[currentWave][x][y+1])/40
            
            xnew = x + Xoffset
            ynew = y + Yoffset
            
            xnew = boundary(xnew, 0, w-1)
            ynew = boundary(ynew, 0, h-1)
            
            shading = (Xoffset - Yoffset) / 2
            
            idx = xnew + ynew*w
            pr = <int>(r[idx] + shading)
            pg = <int>(g[idx] + shading)
            pb = <int>(b[idx] + shading)
            pr = boundary(pr, 0, 255)
            pg = boundary(pg, 0, 255)
            pb = boundary(pb, 0, 255)
            
            idx = (x + y * w) * 3
            render[idx] = pr
            render[idx+1] = pg
            render[idx+2] = pb

