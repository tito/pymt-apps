cdef extern from "math.h":
    double sqrt(double)
    double cos(double)
    double sin(double)

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

