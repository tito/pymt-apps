'''
Some experimentations with shaders
'''


from pymt import *
from OpenGL.GL import *
import os
import time

# some facilities
ww, wh = ws = getWindow().size
w2, h2 = ww / 2., wh / 2.

def shader_load(filename):
	f = open(os.path.join(os.path.dirname(__file__),'shaders',filename), 'r')
	d = f.read()
	f.close()
	return d

	
# shader from http://www.geeks3d.com/20091116/shader-library-2d-shockwave-post-processing-filter-glsl/
class ShadShock(MTWidget):
	title = 'Shock Wave'
	author = 'Geeks3D'
	
	def __init__(self, **kwargs):
		super(ShadShock, self).__init__(**kwargs)
		
		self.width = ww
		self.height = wh
		self.timer = 0
		
		self.shader = Shader(shader_load('std_vertex.txt'), shader_load('shock_fragment.txt'))
		
		self.mouseX = 0.0
		self.mouseY = 0.0
		
		w,h = self.size
		
		self.bg = Image.load(os.path.join(os.path.dirname(__file__), 'ressource/07.jpg'))
		self.bg.scale = max(float(self.height)/self.bg.height,float(self.width)/self.bg.width)
		self.fbo = Fbo(size=(w,h))
  

	def on_touch_down(self, touch):
		self.mouseX = touch.x
		self.mouseY = touch.y
		self.timer = time.time()
	
	def on_touch_up(self,touch):
		pass
		#self.timer = 0
	
	def on_touch_move(self, touch):
		pass

	def on_update(self):
		pass

	def draw(self):
		w,h = self.size
		set_color(1)
		self.fbo.bind()
		self.bg.draw()
		self.shader.use()
		self.shader['param_x'] = self.mouseX / self.width
		self.shader['param_y'] = self.mouseY / self.height
		self.shader['time'] = time.time() - self.timer
		self.shader['param1'] = 10.0
		self.shader['param2'] = 0.8
		self.shader['param3'] = 0.1
		drawTexturedRectangle(self.fbo.texture, (0,0),(self.width,self.height))
		self.shader.stop()
	
		glColor4f(1,1,1,1)
		
		self.fbo.release()
		drawTexturedRectangle(self.fbo.texture, size=(w,h))


class ShadWave(MTWidget):
	title = 'Wave'
	author = 'Remi'
	
	def __init__(self, **kwargs):
		super(ShadWave, self).__init__(**kwargs)
		
		self.width = ww
		self.height = wh
		
		self.shader = Shader(shader_load('std_vertex.txt'), shader_load('wave_fragment.txt'))
		
		self.mouseX = 0.0
		self.mouseY = 0.0
		
		w,h = self.size
		
		self.bg = Image.load(os.path.join(os.path.dirname(__file__), 'ressource/pebble.jpg'))
		self.bg.scale = max(float(self.height)/self.bg.height,float(self.width)/self.bg.width)
		self.fbo = Fbo(size=(w,h))
  

	def on_touch_up(self, touch):
		self.mouseX = touch.x
		self.mouseY = touch.y
	
	def on_touch_move(self, touch):
		self.mouseX = touch.x
		self.mouseY = touch.y

	def on_update(self):
		pass

	def draw(self):
		w,h = self.size
		set_color(1)
		self.fbo.bind()
		self.bg.draw()
		self.shader.use()
		self.shader['fMouseCoordX'] = self.mouseX
		self.shader['fMouseCoordY'] = self.mouseY
		drawTexturedRectangle(self.fbo.texture, (0,0),(self.width,self.height))
		self.shader.stop()
	
		glColor4f(1,1,1,1)
		
		self.fbo.release()
		drawTexturedRectangle(self.fbo.texture, size=(w,h))

# http://www.iquilezles.org/apps/shadertoy/
class ShadMandel(MTWidget):
	title = 'Mandelbrot'
	author = 'iq'
	
	def __init__(self, **kwargs):
		super(ShadMandel, self).__init__(**kwargs)
		
		self.width = ww
		self.height = wh
		
		self.timer = time.time()
		
		self.shader = Shader(shader_load('std_vertex.txt'), shader_load('mandel_fragment.txt'))
		
		self.mouseX = 0.0
		self.mouseY = 0.0
		
		w,h = self.size
		
		self.fbo = Fbo(size=(w,h))

	def draw(self):
		w,h = self.size
		set_color(1)
		self.fbo.bind()
		self.shader.use()
		self.shader['resX'] = self.width
		self.shader['resY'] = self.height
		self.shader['time'] = time.time() - self.timer
		drawTexturedRectangle(self.fbo.texture, (0,0),(self.width,self.height))
		self.shader.stop()
	
		glColor4f(1,1,1,1)
		
		self.fbo.release()
		drawTexturedRectangle(self.fbo.texture, size=(w,h))


# http://www.iquilezles.org/apps/shadertoy/
class ShadJulia(MTWidget):
	title = 'Julia'
	author = 'iq'
	
	def __init__(self, **kwargs):
		super(ShadJulia, self).__init__(**kwargs)
		
		self.width = ww
		self.height = wh
		
		self.timer = time.time()
		
		self.shader = Shader(shader_load('std_vertex.txt'), shader_load('julia_fragment.txt'))
		
		self.mouseX = 0.0
		self.mouseY = 0.0
		
		w,h = self.size
		
		self.fbo = Fbo(size=(w,h))

	def draw(self):
		w,h = self.size
		set_color(1)
		self.fbo.bind()
		self.shader.use()
		self.shader['resX'] = self.width
		self.shader['resY'] = self.height
		self.shader['time'] = time.time() - self.timer
		drawTexturedRectangle(self.fbo.texture, (0,0),(self.width,self.height))
		self.shader.stop()
	
		glColor4f(1,1,1,1)
		
		self.fbo.release()
		drawTexturedRectangle(self.fbo.texture, size=(w,h))


# http://www.iquilezles.org/apps/shadertoy/
class ShadMonjori(MTWidget):
	title = 'Monjori'
	author = 'Mic'
	
	def __init__(self, **kwargs):
		super(ShadMonjori, self).__init__(**kwargs)
		
		self.width = ww
		self.height = wh
		
		self.timer = time.time()
		
		self.shader = Shader(shader_load('std_vertex.txt'), shader_load('monjori_fragment.txt'))
		
		self.mouseX = 0.0
		self.mouseY = 0.0
		
		w,h = self.size
		
		self.fbo = Fbo(size=(w,h))

	def draw(self):
		w,h = self.size
		set_color(1)
		self.fbo.bind()
		self.shader.use()
		self.shader['resX'] = self.width
		self.shader['resY'] = self.height
		self.shader['time'] = time.time() - self.timer
		drawTexturedRectangle(self.fbo.texture, (0,0),(self.width,self.height))
		self.shader.stop()
	
		glColor4f(1,1,1,1)
		
		self.fbo.release()
		drawTexturedRectangle(self.fbo.texture, size=(w,h))

# http://www.iquilezles.org/apps/shadertoy/
class ShadDeform(MTWidget):
	title = 'Deform'
	author = 'iq'
	
	def __init__(self, **kwargs):
		super(ShadDeform, self).__init__(**kwargs)
		
		self.width = ww
		self.height = wh
		self.timer = time.time()
		
		self.shader = Shader(shader_load('std_vertex.txt'), shader_load('deform_fragment.txt'))
		
		self.mouseX = 0.0
		self.mouseY = 0.0
		
		w,h = self.size
		
		self.bg = Image.load(os.path.join(os.path.dirname(__file__), 'ressource/pebble.jpg'))
		self.bg.scale = max(float(self.height)/self.bg.height,float(self.width)/self.bg.width)
		self.fbo = Fbo(size=(w,h))
  

	def on_touch_up(self, touch):
		self.mouseX = touch.x
		self.mouseY = touch.y
	
	def on_touch_move(self, touch):
		self.mouseX = touch.x
		self.mouseY = touch.y

	def on_update(self):
		pass

	def draw(self):
		w,h = self.size
		set_color(1)
		self.fbo.bind()
		self.bg.draw()
		self.shader.use()
		self.shader['resX'] = self.width
		self.shader['resY'] = self.height
		self.shader['mouseX'] = self.mouseX
		self.shader['mouseY'] = self.mouseY
		self.shader['time'] = time.time() - self.timer
		drawTexturedRectangle(self.fbo.texture, (0,0),(self.width,self.height))
		self.shader.stop()
	
		glColor4f(1,1,1,1)
		
		self.fbo.release()
		drawTexturedRectangle(self.fbo.texture, size=(w,h))

# http://www.iquilezles.org/apps/shadertoy/
class ShadClod(MTWidget):
	title = 'Clod'
	author = 'Tigrou'
	
	def __init__(self, **kwargs):
		super(ShadClod, self).__init__(**kwargs)
		
		self.width = ww
		self.height = wh
		
		self.timer = time.time()
		
		self.shader = Shader(shader_load('std_vertex.txt'), shader_load('clod_fragment.txt'))
		
		self.mouseX = 0.0
		self.mouseY = 0.0
		
		w,h = self.size
		
		self.fbo = Fbo(size=(w,h))

	def draw(self):
		w,h = self.size
		set_color(1)
		self.fbo.bind()
		self.shader.use()
		self.shader['resX'] = self.width
		self.shader['resY'] = self.height
		self.shader['time'] = time.time() - self.timer
		drawTexturedRectangle(self.fbo.texture, (0,0),(self.width,self.height))
		self.shader.stop()
	
		glColor4f(1,1,1,1)
		
		self.fbo.release()
		drawTexturedRectangle(self.fbo.texture, size=(w,h))

# http://www.iquilezles.org/apps/shadertoy/
class ShadMetatunnel(MTWidget):
	title = 'Metatunnel'
	author = 'TX95'
	
	def __init__(self, **kwargs):
		super(ShadMetatunnel, self).__init__(**kwargs)
		
		self.width = ww
		self.height = wh
		
		self.timer = time.time()
		
		self.shader = Shader(shader_load('std_vertex.txt'), shader_load('metatunnel_fragment.txt'))
		
		self.mouseX = 0.0
		self.mouseY = 0.0
		
		w,h = self.size
		
		self.fbo = Fbo(size=(w,h))

	def draw(self):
		w,h = self.size
		set_color(1)
		self.fbo.bind()
		self.shader.use()
		self.shader['resX'] = self.width
		self.shader['resY'] = self.height
		self.shader['time'] = time.time() - self.timer
		drawTexturedRectangle(self.fbo.texture, (0,0),(self.width,self.height))
		self.shader.stop()
	
		glColor4f(1,1,1,1)
		
		self.fbo.release()
		drawTexturedRectangle(self.fbo.texture, size=(w,h))

# http://www.iquilezles.org/apps/shadertoy/
class ShadRibbon(MTWidget):
	title = 'To The Road Of Ribbon'
	author = 'TX95'
	
	def __init__(self, **kwargs):
		super(ShadRibbon, self).__init__(**kwargs)
		
		self.width = ww
		self.height = wh
		
		self.timer = time.time()
		
		self.shader = Shader(shader_load('std_vertex.txt'), shader_load('ribbon_fragment.txt'))
		
		self.mouseX = 0.0
		self.mouseY = 0.0
		
		w,h = self.size
		
		self.fbo = Fbo(size=(w,h))

	def draw(self):
		w,h = self.size
		set_color(1)
		self.fbo.bind()
		self.shader.use()
		self.shader['resX'] = self.width
		self.shader['resY'] = self.height
		self.shader['time'] = time.time() - self.timer
		drawTexturedRectangle(self.fbo.texture, (0,0),(self.width,self.height))
		self.shader.stop()
	
		glColor4f(1,1,1,1)
		
		self.fbo.release()
		drawTexturedRectangle(self.fbo.texture, size=(w,h))

# http://www.iquilezles.org/apps/shadertoy/
class ShadQuaternion(MTWidget):
	title = 'Quaternion'
	author = 'iq'
	
	def __init__(self, **kwargs):
		super(ShadQuaternion, self).__init__(**kwargs)
		
		self.width = ww
		self.height = wh
		
		self.timer = time.time()
		
		self.shader = Shader(shader_load('std_vertex.txt'), shader_load('quaternion_fragment.txt'))
		
		self.mouseX = 0.0
		self.mouseY = 0.0
		
		w,h = self.size
		
		self.fbo = Fbo(size=(w,h))

	def draw(self):
		w,h = self.size
		set_color(1)
		self.fbo.bind()
		self.shader.use()
		self.shader['resX'] = self.width
		self.shader['resY'] = self.height
		self.shader['time'] = time.time() - self.timer
		drawTexturedRectangle(self.fbo.texture, (0,0),(self.width,self.height))
		self.shader.stop()
	
		glColor4f(1,1,1,1)
		
		self.fbo.release()
		drawTexturedRectangle(self.fbo.texture, size=(w,h))

# http://www.iquilezles.org/apps/shadertoy/
class ShadSult(MTWidget):
	title = 'Sult'
	author = 'Loonies'
	
	def __init__(self, **kwargs):
		super(ShadSult, self).__init__(**kwargs)
		
		self.width = ww
		self.height = wh
		
		self.timer = time.time()
		
		self.shader = Shader(shader_load('std_vertex.txt'), shader_load('sult_fragment.txt'))
		
		self.mouseX = 0.0
		self.mouseY = 0.0
		
		w,h = self.size
		
		self.fbo = Fbo(size=(w,h))

	def draw(self):
		w,h = self.size
		set_color(1)
		self.fbo.bind()
		self.shader.use()
		self.shader['resX'] = self.width
		self.shader['resY'] = self.height
		self.shader['time'] = time.time() - self.timer
		drawTexturedRectangle(self.fbo.texture, (0,0),(self.width,self.height))
		self.shader.stop()
	
		glColor4f(1,1,1,1)
		
		self.fbo.release()
		drawTexturedRectangle(self.fbo.texture, size=(w,h))

# http://www.iquilezles.org/apps/shadertoy/
class ShadSlisesix(MTWidget):
	title = 'Slisesix'
	author = 'iq'
	
	def __init__(self, **kwargs):
		super(ShadSlisesix, self).__init__(**kwargs)
		
		self.width = ww
		self.height = wh
		
		self.timer = time.time()
		
		self.shader = Shader(shader_load('std_vertex.txt'), shader_load('slisesix_fragment.txt'))
		
		self.mouseX = 0.0
		self.mouseY = 0.0
		
		w,h = self.size
		
		self.fbo = Fbo(size=(w,h))

	def draw(self):
		w,h = self.size
		set_color(1)
		self.fbo.bind()
		self.shader.use()
		self.shader['resX'] = self.width
		self.shader['resY'] = self.height
		self.shader['time'] = time.time() - self.timer
		drawTexturedRectangle(self.fbo.texture, (0,0),(self.width,self.height))
		self.shader.stop()
	
		glColor4f(1,1,1,1)
		
		self.fbo.release()
		drawTexturedRectangle(self.fbo.texture, size=(w,h))

#
# Main class for control
#

class VizPlay(MTWidget):
	def __init__(self, **kwargs):
		super(VizPlay, self).__init__(**kwargs)
		self.scenarios = []
		self.current = None
		self.nextidx = 0
		self.state = 0
		self.out_alpha = 0
		self.info_alpha = 1

	def add_scenario(self, scn):
		if self.current is None:
			self.current = scn
			self.add_widget(self.current)
		self.scenarios.append(scn)

	def on_touch_down(self, touch):
		if touch.y < 70:
			if touch.x < 100:
				self.goto(-1)
				return True
			if touch.x > ww - 100:
				self.goto(1)
				return True
		return super(VizPlay, self).on_touch_down(touch)

	def goto(self, s):
		self.nextidx = (self.nextidx + s) % len(self.scenarios)
		self.state = 1

	def on_draw(self):
		d = getFrameDt() * 2.
		# state machine
		if self.state == 1:
			# fade out the current screen
			self.delay = 0
			self.out_alpha += d
			if self.out_alpha >= 1.:
				self.out_alpha = 1
				self.state = 2
		elif self.state == 2:
			# change screen
			self.remove_widget(self.current)
			self.current = self.scenarios[self.nextidx]
			self.add_widget(self.current)
			self.state = 3
		elif self.state == 3:
			self.info_alpha = 1
			self.out_alpha -= d
			if self.out_alpha <= 0:
				self.out_alpha = 0
				self.state = 4
		elif self.state == 4:
			self.delay += d / 2.
			if self.delay >= 3:
				self.delay = 0
				self.state = 5
		elif self.state == 5:
			self.info_alpha -= d / 6.
			if self.info_alpha <= 0:
				self.state = 0

		# background
		set_color(0)
		drawRectangle(size=ws)

		# us
		super(VizPlay, self).on_draw()

		# info alpha
		ia = self.info_alpha

		# bottom bar
		set_color(59/255., 126/255., 197/255., .3 * ia)
		drawRectangle(size=(ww, 50))

		# title
		drawLabel(label=self.current.title,
				  font_size=22,
				  color=(1, 1, 1, .7 * ia),
				  pos=(w2, 30))
		drawLabel(label=self.current.author,
                  font_size=10,
                  color=(1, 1, 1, .5 * ia),
                  pos=(w2, 12))
		# next / previous
		drawLabel(label='<',
				  font_size=42,
				  color=(.8, .8, 1, .4),
				  pos=(30, 25))

		# previous
		drawLabel(label='>',
				  font_size=42,
				  color=(.8, .8, 1, .4),
				  pos=(ww - 30, 25))

		# draw FPS
		drawLabel(label='%.2f' % getClock().get_fps(),
				  font_size=20,
				  color=(.8, .8, .8, .4),
				  pos=(10, wh - 36),
				  center=False)


		# out
		if self.out_alpha > 0:
			set_color(0, 0, 0, self.out_alpha)
			drawRectangle(size=ws)

if __name__ == '__main__':
	viz = VizPlay()
	viz.add_scenario(ShadShock())
	viz.add_scenario(ShadSult())
	viz.add_scenario(ShadQuaternion())
	viz.add_scenario(ShadRibbon())
	viz.add_scenario(ShadMetatunnel())
	viz.add_scenario(ShadClod())
	viz.add_scenario(ShadDeform())
	viz.add_scenario(ShadMonjori())
	viz.add_scenario(ShadJulia())
	viz.add_scenario(ShadMandel())
	viz.add_scenario(ShadWave())
	viz.add_scenario(ShadSlisesix())
	
	runTouchApp(viz)
