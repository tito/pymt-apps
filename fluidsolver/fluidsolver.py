'''
Fluid solver, based on MSAFluid

This is a work in progress, this code is only here for beta testing.

Mathieu

TODO:
    * fix doVorticityConfinement
    * write doc
    * include particles
    * move fluid to pymt
'''

import sys
try:
    import pyximport
    pyximport.install()
except Exception, e:
    print 'This application require Cython + an environment for compilation !'
    print 'This will change in a future.'
    print e
    sys.exit(1)

try:
    from c_fluidsolver import FluidSolver
except Exception, e:
    print 'Unable to import compiled FluidSolver, cannot run.'
    print e
    sys.exit(1)

from pymt import *

class MTFluid(MTWidget):
    def __init__(self, **kwargs):
        super(MTFluid, self).__init__(**kwargs)
        self.ratio = self.height / float(self.width)
        self._precision = kwargs.get('precision', 120)
        self._rgb = kwargs.get('rgb', True)
        self._fadespeed = kwargs.get('fadespeed', .003)
        self._viscosity = kwargs.get('viscosity', .0001)
        self._iterations = kwargs.get('iterations', 5)
        self._colordiffusion = kwargs.get('colordiffusion', 0.0001)
        self._contrast = kwargs.get('contrast', 5)
        self._speed = kwargs.get('speed', 5)
        self._wrapx = kwargs.get('wrapx', False)
        self._wrapy = kwargs.get('wrapy', False)
        self.setup()

    def on_resize(self, w, h):
        self.setup()

    def setup(self):
        w = self._precision
        h = w * self.ratio
        self.solver = FluidSolver(w, h)
        self.solver.rgb = self._rgb
        self.solver.fadespeed = self._fadespeed
        self.solver.viscosity = self._viscosity
        self.solver.solveriterations = self._iterations
        self.solver.colordiffusion = self._colordiffusion
        self.solver.wrapx = self._wrapx
        self.solver.wrapy = self._wrapy

    def on_update(self):
        self.solver.update(getFrameDt() * self._speed)

    def on_touch_down(self, touch):
        self.solver.addForce(touch.sx, touch.sy * self.ratio, 0, 0)

    def on_touch_move(self, touch):
        d = (Vector(touch.pos) - Vector(touch.dpos))
        self.solver.addForce(touch.sx, touch.sy * self.ratio, d.x, d.y)

    def draw(self):
        self.solver.draw_into_texture(self._contrast)
        #self.solver.draw_into_texture_motion()
        #self.solver.draw_into_texture_speed()
        set_color(1, 1, 1)
        drawTexturedRectangle(texture=self.solver.texture, size=self.size)

if __name__ == '__main__':
    fluid = MTFluid(size=getWindow().size)

    runTouchApp(fluid)
