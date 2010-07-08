'''
Python/Cython port of MSAFluid

Copyright (c) 2008, 2009, Memo Akten, www.memo.tv
Copyright (c) 2010, Mathieu Virbel, txzone.net

This port require PyMT/PyOpenGL for texture creation


TODO:
 * fix doVorticityConfinement


*** The Mega Super Awesome Visuals Company ***

This is a class for solving real-time fluid dynamics simulations
based on Navier-Stokes equations and code from Jos Stam's paper
"Real-Time Fluid Dynamics for Games"
http://www.dgp.toronto.edu/people/stam/reality/Research/pdf/GDC03.pdf

Other useful resources and implementations I looked at while building this lib:
* Mike Ash (C) - http://mikeash.com/?page=pyblog/fluid-simulation-for-dummies.html
* Alexander McKenzie (Java) - http://www.multires.caltech.edu/teaching/demos/java/stablefluids.htm
* Pierluigi Pesenti (AS3 port of Alexander's) - http://blog.oaxoa.com/2008/01/21/actionscript-3-fluids-simulation/
* Gustav Taxen (C) - http://www.nada.kth.se/~gustavt/fluids/
* Dave Wallin (C++) - http://nuigroup.com/touchlib/ (uses portions from Gustav's)
'''

from pymt import Texture
from OpenGL.GL import *

# malloc, free
from stdlib cimport *

cdef import from "math.h":
    double sqrt(double)

cdef import from "Python.h":
    object PyString_FromStringAndSize(char *, Py_ssize_t)

cdef import from "strings.h":
    void bzero(void *s, int n)

cdef hsb2grb(int h=1, int s=1, int b=1):
    h = <int>h % 360
    i = int(int(h / 60.0) % 6)
    f = h / 60.0 - int(h / 60.0)
    p = b * (1 - s)
    q = b * (1 - s * f)
    t = b * (1 - (1 - f) * s)
    if   i == 0: return (b, t, p)
    elif i == 1: return (q, b, p)
    elif i == 2: return (p, b, t)
    elif i == 3: return (p, q, b)
    elif i == 4: return (t, p, b)
    elif i == 5: return (b, p, q)
    return (0, 0, 0)

cdef inline int int_max(int a, int b): return a if a >= b else b
cdef inline int int_min(int a, int b): return a if a <= b else b
cdef inline double double_max(double a, double b): return a if a >= b else b
cdef inline double double_min(double a, double b): return a if a <= b else b

cdef double *null = <double *>0

cdef class FluidSolver(object):

    cdef public int frameCount
    cdef public int width, height, numCells
    cdef public int solveriterations
    cdef public bint doVorticityConfinement, wrapx, wrapy, rgb
    cdef public double colordiffusion, viscosity, fadespeed
    cdef public object texture

    cdef int _NX, _NY, _NX2, _NY2
    cdef double _invNumCells, _dt
    cdef double _aspectRatio
    cdef double _avgDensity, _avgSpeed, _uniformity
    cdef double *r, *rOld, *g, *gOld, *b, *bOld, *u, *uOld, *v, *vOld, *curl_abs, *curl_orig
    cdef char *_buffer
    cdef int _buffer_len

    def __cinit__(self):
        self.frameCount             = 0
        self.width                  = 0
        self.height                 = 0
        self.numCells               = 0
        self._NX                    = 0
        self._NY                    = 0
        self._NX2                   = 0
        self._NY2                   = 0
        self._invNumCells           = 0
        self._dt                    = 0.
        self.rgb                    = False
        self.solveriterations       = 0
        self.colordiffusion         = 0.
        self.doVorticityConfinement = False
        self.wrapx                  = False
        self.wrapy                  = False
        self.viscosity              = 0.
        self.fadespeed              = 0.
        self._avgDensity            = 0.
        self._uniformity            = 0.
        self._avgSpeed              = 0.
        self.r = self.rOld = self.g = self.gOld = self.b = self.bOld = null
        self.u = self.uOld = self.v = self.vOld = null
        self.curl_abs = self.curl_orig = null
        self.texture                = None

    def __dealloc__(self):
        if self.r != null:
            free(self.r)
            self.r = null
        if self.rOld != null:
            free(self.rOld)
            self.rOld = null
        if self.g != null:
            free(self.g)
            self.g = null
        if self.gOld != null:
            free(self.gOld)
            self.gOld = null
        if self.b != null:
            free(self.b)
            self.b = null
        if self.bOld != null:
            free(self.bOld)
            self.bOld = null
        if self.u != null:
            free(self.u)
            self.u = null
        if self.uOld != null:
            free(self.uOld)
            self.uOld = null
        if self.v != null:
            free(self.v)
            self.v = null
        if self.vOld != null:
            free(self.vOld)
            self.vOld = null
        if self.curl_abs != null:
            free(self.curl_abs)
            self.curl_abs = null
        if self.curl_orig != null:
            free(self.curl_orig)
            self.curl_orig = null

    def __init__(self, int NX, int NY):
        NX += 2
        NY += 2
        self.setup(NX, NY)

    cdef setup(self, int NX, int NY):
        self._dt                    = 1.0
        self.fadespeed              = 0.
        self.solveriterations       = 5
        self.colordiffusion         = 0.0001
        self.doVorticityConfinement = 0
        self._NX                    = NX
        self._NY                    = NY
        self._NX2                   = self._NX + 2
        self._NY2                   = self._NY + 2
        self._aspectRatio           = <float>NY / <float>NX
        self.numCells               = self._NX2 * self._NY2
        self._invNumCells           = 1.0 / self.numCells
        self.width                  = self._NX2
        self.height                 = self._NY2
        self.rgb                    = False

        self.reset()

    cdef reset(self):
        cdef int l = self.numCells * sizeof(double)
        self.r         = <double *>malloc(l)
        self.rOld      = <double *>malloc(l)
        self.g         = <double *>malloc(l)
        self.gOld      = <double *>malloc(l)
        self.b         = <double *>malloc(l)
        self.bOld      = <double *>malloc(l)
        self.u         = <double *>malloc(l)
        self.uOld      = <double *>malloc(l)
        self.v         = <double *>malloc(l)
        self.vOld      = <double *>malloc(l)
        self.curl_abs  = <double *>malloc(l)
        self.curl_orig = <double *>malloc(l)

        bzero(<void *>self.r, l)
        bzero(<void *>self.rOld, l)
        bzero(<void *>self.g, l)
        bzero(<void *>self.gOld, l)
        bzero(<void *>self.b, l)
        bzero(<void *>self.bOld, l)
        bzero(<void *>self.u, l)
        bzero(<void *>self.uOld, l)
        bzero(<void *>self.v, l)
        bzero(<void *>self.vOld, l)
        bzero(<void *>self.curl_abs, l)
        bzero(<void *>self.curl_orig, l)

    cpdef update(self, double dt):
        '''this must be called once every frame to move the solver one step forward'''
        self._dt = dt
        self.frameCount = (self.frameCount + 1) % 0xffffffff

        self.addSourceUV()

        if self.doVorticityConfinement:
            self.calcVorticityConfinement(self.uOld, self.vOld)
            self.addSourceUV()

        self.swapUV()

        self.diffuseUV(self.viscosity)

        self.project(self.u, self.v, self.uOld, self.vOld)

        self.swapUV()

        self.advect(1, self.u, self.uOld, self.uOld, self.vOld)
        self.advect(2, self.v, self.vOld, self.uOld, self.vOld)

        self.project(self.u, self.v, self.uOld, self.vOld)

        if self.rgb:
            self.addSourceRGB()
            self.swapRGB()

            if self.colordiffusion != 0 and self._dt != 0:
                self.diffuseRGB(self.colordiffusion)
                self.swapRGB()

            self.advectRGB(self.u, self.v)

            self.fadeRGB()
        else:
            self.addSource(self.r, self.rOld)
            self.swapR()

            if self.colordiffusion != 0 and self._dt != 0:
                self.diffuse(0, self.r, self.rOld, self.colordiffusion)
                self.swapRGB()

            self.advect(0, self.r, self.rOld, self.u, self.v)
            self.fadeR()

    cdef calcVorticityConfinement(self, double *_x, double *_y):
        cdef double dw_dx  = 0.
        cdef double dw_dy  = 0.
        cdef int i      = 0
        cdef int j      = 0
        cdef double length = 0.
        cdef int index  = 0
        cdef double vv     = 0.

        # Calculate magnitude of (u,v) for each cell. (|w|)
        for j in xrange(self._NY, 0, -1):
            index = self.fluid_index(self._NX, j)
            for i in xrange(self._NX, 0, -1):
                dw_dy = self.u[<int>(index + self._NX2)] - self.u[<int>(index - self._NX2)]
                dw_dx = self.v[<int>(index + 1)] - self.v[<int>(index - 1)]

                vv = (dw_dy - dw_dx) * .5

                self.curl_orig[index] = vv
                if vv < 0:
                    vv = -vv
                self.curl_abs[index] = vv

                index -= 1

        for j in xrange(self._NY-1, 1, -1):
            index = self.fluid_index(self._NX-1, j)
            for i in xrange(self._NX-1, 1, -1):
                dw_dx = self.curl_abs[<int>(index + 1)] - self.curl_abs[<int>(index - 1)]
                dw_dy = self.curl_abs[<int>(index + self._NX2)] - self.curl_abs[<int>(index - self._NX2)]

                length = sqrt(dw_dx * dw_dx + dw_dy * dw_dy) + 0.000001

                length = 2 / length
                dw_dx *= length
                dw_dy *= length

                vv = self.curl_orig[index]

                _x[index] = dw_dy * -vv
                _y[index] = dw_dx * vv

                index -= 1

    cdef fadeR(self):
        cdef double holdAmount = 1 - self.fadespeed
        cdef double totalDeviations = 0.
        cdef double tmp_r, currentDeviation
        cdef int i

        self._avgDensity = 0
        self._avgSpeed = 0

        for i in xrange(self.numCells-1, -1, -1):
            # clear old values
            self.uOld[i] = self.vOld[i] = 0
            self.rOld[i] = 0

            # calc avg speed
            self._avgSpeed += self.u[i] * self.u[i] + self.v[i] * self.v[i]

            # calc avg density
            tmp_r = double_min(1.0, self.r[i])
            self._avgDensity += tmp_r    # add it up

            # calc deviation (for uniformity)
            currentDeviation = tmp_r - self._avgDensity
            totalDeviations += currentDeviation * currentDeviation

            # fade out old
            self.r[i] = tmp_r * holdAmount

        self._avgDensity *= self._invNumCells
        self._uniformity = 1.0 / (1 + totalDeviations * self._invNumCells)        # 0: very wide distribution, 1: very uniform


    def fadeRGB(self):
        cdef double holdAmount = 1 - self.fadespeed
        cdef double totalDeviations = 0.
        cdef double tmp_r, tmp_g, tmp_b,
        cdef double currentDeviation, density
        cdef int i

        holdAmount = 1 - self.fadespeed

        self._avgDensity = 0
        self._avgSpeed = 0

        totalDeviations = 0

        for i in xrange(self.numCells-1, -1, -1):
            # clear old values
            self.uOld[i] = self.vOld[i] = 0
            self.rOld[i] = 0
            self.gOld[i] = self.bOld[i] = 0

            # calc avg speed
            self._avgSpeed += self.u[i] * self.u[i] + self.v[i] * self.v[i]

            # calc avg density
            tmp_r = double_min(1.0, self.r[i])
            tmp_g = double_min(1.0, self.g[i])
            tmp_b = double_min(1.0, self.b[i])

            density = double_max(tmp_r, double_max(tmp_g, tmp_b))
            self._avgDensity += density

            # calc deviation (for uniformity)
            currentDeviation = density - self._avgDensity
            totalDeviations += currentDeviation * currentDeviation

            # fade out old
            self.r[i] = tmp_r * holdAmount
            self.g[i] = tmp_g * holdAmount
            self.b[i] = tmp_b * holdAmount

        self._avgDensity *= self._invNumCells
        self._avgSpeed *= self._invNumCells

        self._uniformity = 1.0 / (1 + totalDeviations * self._invNumCells); # 0: very wide distribution, 1: very uniform

    cdef addSourceUV(self):
        cdef int i
        for i in xrange(self.numCells-1, -1, -1):
            self.u[i] += self._dt * self.uOld[i]
            self.v[i] += self._dt * self.vOld[i]

    cdef addSourceRGB(self):
        cdef int i
        for i in xrange(self.numCells-1, -1, -1):
            self.r[i] += self._dt * self.rOld[i]
            self.g[i] += self._dt * self.gOld[i]
            self.b[i] += self._dt * self.bOld[i]

    cdef addSource(self, double *x, double *x0):
        cdef int i
        for i in xrange(self.numCells-1, -1, -1):
            x[i] += self._dt * x0[i]

    cdef advect(self, int b, double *_d, double *d0, double *du, double *dv):

        cdef double x, y, dt0x, dt0y, s0, s1, t0, t1
        cdef int i, j, index, i0, i1, j0, j1

        dt0x = self._dt * self._NX
        dt0y = self._dt * self._NY

        for j in xrange(self._NY, 0, -1):
            for i in xrange(self._NX, 0, -1):

                index = self.fluid_index(i, j)

                x = i - dt0x * du[index]
                y = j - dt0y * dv[index]

                if x > self._NX + 0.5:
                    x = self._NX + 0.5
                if x < 0.5:
                    x = 0.5

                i0 = <int>(x)
                i1 = i0 + 1

                if y > self._NY + 0.5:
                    y = self._NY + 0.5
                if y < 0.5:
                    y = 0.5

                j0 = <int>(y)
                j1 = j0 + 1

                s1 = x - i0
                s0 = 1 - s1
                t1 = y - j0
                t0 = 1 - t1

                _d[index] = (s0 * (t0 * d0[self.fluid_index(i0, j0)] +
                            t1 * d0[self.fluid_index(i0, j1)]) +
                            s1 * (t0 * d0[self.fluid_index(i1, j0)] +
                            t1 * d0[self.fluid_index(i1, j1)]))

        self.setBoundary(b, _d)

    cdef advectRGB(self, double *du, double *dv):
        cdef double x, y, dt0x, dt0y, s0, s1, t0, t1
        cdef int i, j, index, i0, i1, j0, j1

        dt0x = self._dt * self._NX
        dt0y = self._dt * self._NY

        for j in xrange(self._NY, 0, -1):
            for i in xrange(self._NX, 0, -1):
                index = self.fluid_index(i, j)
                x = i - dt0x * du[index]
                y = j - dt0y * dv[index]

                if x > self._NX + 0.5:
                    x = self._NX + 0.5
                if x < 0.5:
                    x = 0.5

                i0 = <int>(x)

                if y > self._NY + 0.5:
                    y = self._NY + 0.5
                if y < 0.5:
                    y = 0.5

                j0 = <int>(y)

                s1 = x - i0
                s0 = 1 - s1
                t1 = y - j0
                t0 = 1 - t1


                i0 = self.fluid_index(i0, j0)
                j0 = i0 + self._NX2
                self.r[index] = s0 * ( t0 * self.rOld[i0] + t1 * self.rOld[j0] \
                    ) + s1 * ( t0 * self.rOld[<int>(i0+1)] + t1 * self.rOld[<int>(j0+1)] )
                self.g[index] = s0 * ( t0 * self.gOld[i0] + t1 * self.gOld[j0] \
                    ) + s1 * ( t0 * self.gOld[<int>(i0+1)] + t1 * self.gOld[<int>(j0+1)] )
                self.b[index] = s0 * ( t0 * self.bOld[i0] + t1 * self.bOld[j0] \
                    ) + s1 * ( t0 * self.bOld[<int>(i0+1)] + t1 * self.bOld[<int>(j0+1)] )

        self.setBoundaryRGB()

    cdef diffuse(self, long b, double *c, double *c0, double _diff):
        cdef double a
        a = self._dt * _diff * self._NX * self._NY
        self.linearSolver(b, c, c0, a, 1.0 + 4 * a)

    cdef diffuseRGB(self, double _diff):
        cdef double a
        a = self._dt * _diff * self._NX * self._NY
        self.linearSolverRGB(a, 1.0 + 4 * a)

    cdef diffuseUV(self, double _diff):
        cdef double a
        a = self._dt * _diff * self._NX * self._NY
        self.linearSolverUV(a, 1.0 + 4 * a)

    cdef project(self, double *x, double *y, double *p, double *div):

        cdef double h, fx, fy
        cdef int index, i, j

        h = -0.5 / self._NX

        index = self.fluid_index(self._NX, self._NY)
        for j in xrange(self._NY, 0, -1):
            for i in xrange(self._NX, 0, -1):
                div[index] = h * ( x[index+1] - x[index-1] + y[index+self._NX2] - y[index-self._NX2] )
                p[index] = 0
                index -= 1

        self.setBoundary(0, div)
        self.setBoundary(0, p)

        self.linearSolver(0, p, div, 1, 4)

        fx = 0.5 * self._NX
        fy = 0.5 * self._NY
        index = self.fluid_index(self._NX, self._NY)
        for j in xrange(self._NY, 0, -1):
            for i in xrange(self._NX, 0, -1):
                x[index] -= fx * (p[index+1] - p[index-1])
                y[index] -= fy * (p[index+self._NX2] - p[index-self._NX2])
                index -= 1

        self.setBoundary(1, x)
        self.setBoundary(2, y)

    cdef linearSolver(self, long b, double *x, double *x0, double a, double c):
        cdef int i, j, k, index
        if a == 1 and c == 4:
            for k in xrange(self.solveriterations):
                index = self.fluid_index(self._NX, self._NY)
                for j in xrange(self._NY, 0, -1):
                    for i in xrange(self._NX, 0, -1):
                        x[index] = ( x[index-1] + x[index+1] + x[index - self._NX2] + x[index + self._NX2] + x0[index] ) * .25
                        index -= 1
                self.setBoundary( b, x )
        else:
            c = 1. / c
            for k in xrange(self.solveriterations):
                for j in xrange(self._NY, 0, -1):
                    index = self.fluid_index(self._NX, j)
                    for i in xrange(self._NX, 0, -1):
                        x[index] = ( ( x[<int>(index-1)] + x[<int>(index+1)] + x[<int>(index - self._NX2)] + x[<int>(index + self._NX2)] ) * a + x0[index] ) * c
                        index -= 1
                self.setBoundary( b, x )

    cdef linearSolverRGB(self, double a, double c):
        cdef int i, j, k, index, index3, index4

        c = 1 / c

        for k in xrange(self.solveriterations):
            for j in xrange(self._NY, 0, -1):
                index = self.fluid_index(self._NX, j)
                index3 = index - self._NX2
                index4 = index + self._NX2
                for i in xrange(self._NX, 0, -1):
                    self.r[index] = ( ( self.r[<int>(index-1)] + self.r[<int>(index+1)]  +  self.r[index3] + self.r[index4] ) * a  +  self.rOld[index] ) * c
                    self.g[index] = ( ( self.g[<int>(index-1)] + self.g[<int>(index+1)]  +  self.g[index3] + self.g[index4] ) * a  +  self.gOld[index] ) * c
                    self.b[index] = ( ( self.b[<int>(index-1)] + self.b[<int>(index+1)]  +  self.b[index3] + self.b[index4] ) * a  +  self.bOld[index] ) * c

                    index -= 1
                    index3 -= 1
                    index4 -=1

            self.setBoundaryRGB()


    cdef linearSolverUV(self, double a, double c):
        cdef int i, j, k, index, i1, i2, i3, i4
        c = 1 / c
        for k in xrange(self.solveriterations):
            index = self.fluid_index(self._NX, self._NY)
            for j in xrange(self._NY, 0, -1):
                for i in xrange(self._NX, 0, -1):
                    i1 = index - 1
                    i2 = index + 1
                    i3 = index - self._NX2
                    i4 = index + self._NX2
                    self.u[index] = ( ( self.u[i1] + self.u[i2] +
                                        self.u[i3] +
                                        self.u[i4] ) * a  +  self.uOld[index] ) * c
                    self.v[index] = ( ( self.v[i1] + self.v[i2] +
                                        self.v[i3] +
                                        self.v[i4] ) * a  +  self.vOld[index] ) * c
                    index -= 1
            self.setBoundary(1, self.u)
            self.setBoundary(2, self.v)

    cdef setBoundary(self, long bound, double *x):
        cdef int step, src1, src2, dst1, dst2, i

        step = self.fluid_index(0, 1) - self.fluid_index(0, 0)

        dst1 = self.fluid_index(0, 1)
        src1 = self.fluid_index(1, 1)
        dst2 = self.fluid_index(self._NX+1, 1 )
        src2 = self.fluid_index(self._NX, 1)

        if self.wrapx:
            src1 ^= src2
            src2 ^= src1
            src1 ^= src2

        if bound == 1 and not self.wrapx:
            for i in xrange(self._NY, 0, -1):
                x[dst1] = -x[src1]
                dst1 += step
                src1 += step
                x[dst2] = -x[src2]
                dst2 += step
                src2 += step
        else:
            for i in xrange(self._NY, 0, -1):
                x[dst1] = x[src1]
                dst1 += step
                src1 += step
                x[dst2] = x[src2]
                dst2 += step
                src2 += step

        dst1 = self.fluid_index(1, 0)
        src1 = self.fluid_index(1, 1)
        dst2 = self.fluid_index(1, self._NY+1)
        src2 = self.fluid_index(1, self._NY)

        if self.wrapy:
            src1 ^= src2
            src2 ^= src1
            src1 ^= src2

        if bound == 2 and not self.wrapy:
            for i in xrange(self._NX, 0, -1):
                x[dst1] = -x[src1]
                x[dst2] = -x[src2]
                dst1 += 1
                dst2 += 1
                src1 += 1
                src2 += 1
        else:
            for i in xrange(self._NX, 0, -1):
                x[dst1] = x[src1]
                x[dst2] = x[src2]
                dst1 += 1
                dst2 += 1
                src1 += 1
                src2 += 1

        x[self.fluid_index(  0,   0)]               = 0.5 * (x[self.fluid_index(1, 0  )] + x[self.fluid_index(  0, 1)])
        x[self.fluid_index(  0, self._NY+1)]        = 0.5 * (x[self.fluid_index(1, self._NY+1)] + x[self.fluid_index(  0, self._NY)])
        x[self.fluid_index(self._NX+1,   0)]        = 0.5 * (x[self.fluid_index(self._NX, 0  )] + x[self.fluid_index(self._NX+1, 1)])
        x[self.fluid_index(self._NX+1, self._NY+1)] = 0.5 * (x[self.fluid_index(self._NX, self._NY+1)] + x[self.fluid_index(self._NX+1, self._NY)])


    cdef setBoundaryRGB(self):
        cdef int step, src1, src2, dst1, dst2, i

        if not self.wrapx and not self.wrapy:
            return

        step = self.fluid_index(0, 1) - self.fluid_index(0, 0)

        if self.wrapx:
            dst1 = self.fluid_index(0, 1)
            src1 = self.fluid_index(1, 1)
            dst2 = self.fluid_index(self._NX+1, 1 )
            src2 = self.fluid_index(self._NX, 1)

            src1 ^= src2
            src2 ^= src1
            src1 ^= src2

            for i in xrange(self._NY, 0, -1):
                self.r[dst1] = self.r[src1]
                self.g[dst1] = self.g[src1]
                self.b[dst1] = self.b[src1]
                dst1 += step
                src1 += step
                self.r[dst2] = self.r[src2]
                self.g[dst2] = self.g[src2]
                self.b[dst2] = self.b[src2]
                dst2 += step
                src2 += step

        if self.wrapy:
            dst1 = self.fluid_index(1, 0)
            src1 = self.fluid_index(1, 1)
            dst2 = self.fluid_index(1, self._NY+1)
            src2 = self.fluid_index(1, self._NY)

            src1 ^= src2
            src2 ^= src1
            src1 ^= src2

            for i in xrange(self._NX, 0, -1):
                self.r[dst1] = self.r[src1]
                self.g[dst1] = self.g[src1]
                self.b[dst1] = self.b[src1]
                dst1 += 1
                src1 += 1
                self.r[dst2] = self.r[src2]
                self.g[dst2] = self.g[src2]
                self.b[dst2] = self.b[src2]
                dst2 += 1
                src2 += 1

    cdef swapUV(self):
        cdef double *_tmp
        _tmp = self.u
        self.u = self.uOld
        self.uOld = _tmp

        _tmp = self.v
        self.v = self.vOld
        self.vOld = _tmp

    cdef swapR(self):
        cdef double *_tmp
        _tmp = self.r
        self.r = self.rOld
        self.rOld = _tmp

    cdef swapRGB(self):
        cdef double *_tmp
        _tmp = self.r
        self.r = self.rOld
        self.rOld = _tmp

        _tmp = self.g
        self.g = self.gOld
        self.gOld = _tmp

        _tmp = self.b
        self.b = self.bOld
        self.bOld = _tmp

    cdef int fluid_index(self, int i, int j):
        return i + self._NX2 * j

    cdef getIndexForCellPosition(self, int i, int j):
        if i < 1:
            i = 1
        elif i > self._NX:
            i = self._NX
        if j < 1:
            j = 1
        elif j > self._NY:
            j = self._NY
        return self.fluid_index(i, j)

    cdef int getIndexForNormalizedPosition(self, double x, double y):
        return self.getIndexForCellPosition(int(x * self._NX2), int(y * self._NX2))

    def addForce(self, double x, double y, double dx, double dy,
                 double colorMult=30):
        cdef int index
        cdef double speed, hue

        speed = dx * dx  + dy * dy * self._aspectRatio * self._aspectRatio

        if speed > 0:
            x = double_min(1, max(x, 0))
            y = double_min(1, max(y, 0))

            index = self.getIndexForNormalizedPosition(x, y);

            hue = ((x + y) * 180 + self.frameCount) % 360;

            r, g, b = hsb2grb(<int>hue);

            self.rOld[index] += r * colorMult;
            self.gOld[index] += g * colorMult;
            self.bOld[index] += b * colorMult;

            self.uOld[index] += dx;
            self.vOld[index] += dy;

    cdef ensure_texture(self):
        if self.texture is not None:
            return
        self.texture = Texture.create(self.width - 2, self.height - 2, format=GL_RGB)
        l = 3 * (self.width - 2) * (self.height - 2) * sizeof(char)
        self._buffer = <char *>malloc(l)
        for i in xrange(l):
            self._buffer[i] = 0
        self._buffer_len = l

    def draw_into_texture(self, double contrast=1):
        cdef int i, j, tw, th, fw, d, fi, index, l

        self.ensure_texture()

        d = <int>(255. * contrast)
        fw = self.width
        tw = fw - 1
        th = self.height - 1
        index = 0

        for j in xrange(1, th):
            for i in xrange(1, tw):
                fi = <int>(i + fw * j)
                self._buffer[index] = <char>(int_min(255, <int>(self.r[fi] * d)))
                index += 1
                self._buffer[index] = <char>(int_min(255, <int>(self.g[fi] * d)))
                index += 1
                self._buffer[index] = <char>(int_min(255, <int>(self.b[fi] * d)))
                index += 1

        a = PyString_FromStringAndSize(self._buffer, self._buffer_len)
        self.texture.blit_buffer(a)

    def draw_motion_into_texture(self):
        cdef int i, j, tw, th, fw, d, fi, index, l

        self.ensure_texture()

        d = 0xff
        fw = self.width
        tw = fw - 1
        th = self.height - 1
        index = 0

        for j in xrange(1, th):
            for i in xrange(1, tw):
                fi = <int>(i + fw * j)
                self._buffer[index] = <char>(<int>(self.u[fi] * d) % 255)
                index += 1
                self._buffer[index] = <char>(<int>(self.v[fi] * d) % 255)
                index += 1
                self._buffer[index] = 0
                index += 1

        a = PyString_FromStringAndSize(self._buffer, self._buffer_len)
        self.texture.blit_buffer(a)

    def draw_speed_into_texture(self):
        cdef int i, j, tw, th, fw, fi, index, l

        self.ensure_texture()

        fw = self.width
        tw = fw - 1
        th = self.height - 1
        index = 0

        for j in xrange(1, th):
            for i in xrange(1, tw):
                speed = self.u[fi] * tw + self.v[fi] * th
                fi = <int>(i + fw * j)
                self._buffer[index] = <char>(<int>(speed) % 255)
                index += 1
                self._buffer[index] = <char>(<int>(speed) % 255)
                index += 1
                self._buffer[index] = <char>(<int>(speed) % 255)
                index += 1

        a = PyString_FromStringAndSize(self._buffer, self._buffer_len)
        self.texture.blit_buffer(a)
