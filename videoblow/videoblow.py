from pymt import *
from random import *
from math import *
import sys

# PYMT Plugin integration
IS_PYMT_PLUGIN = True
PLUGIN_TITLE = 'Video destruction'
PLUGIN_AUTHOR = 'Remi Pauchet'
PLUGIN_DESCRIPTION = 'Play a video and blow it up!'

'''
shamefully inspired by:
http://craftymind.com/factory/html5video/CanvasVideo.html

video is 640x480 -> tile 20 * 32x24

'''

class VideoExploder(MTWidget):
	def __init__(self, filename, **kwargs):
		super(VideoExploder, self).__init__(**kwargs)
				
		self.player = pymt.Video(filename=filename)
		self.player.play()
		self.player.volume = 0
		self.tx = 32
		self.ty = 24
		

		#(x,y,vecx,vecy,force,orgx,orgy)
		self.current_pos = []
		for i in range(20):
			self.current_pos.append([])
			for j in range(20):
				self.current_pos[i].append([i*self.tx, j*self.ty, 0, 0, 0,i*self.tx, j*self.ty])
		

	def on_update(self):
		self.player.update()
				
	def draw(self):
		ox = (self.width - self.player.width) / 2
		oy = (self.height - self.player.height) / 2
		set_color(1)
		if self.player.texture: #wait for the video at startup...
			for i in range(20):
				for j in range(20):
					if self.current_pos[i][j][4] > 0.0001:
						self.current_pos[i][j][2] *= self.current_pos[i][j][4]
						self.current_pos[i][j][3] *= self.current_pos[i][j][4]
						self.current_pos[i][j][0] += self.current_pos[i][j][2]
						self.current_pos[i][j][1] += self.current_pos[i][j][3]
						self.current_pos[i][j][4] *= 0.9;
						if self.current_pos[i][j][0] <= 0 or self.current_pos[i][j][0] >= self.width:
							self.current_pos[i][j][0] *= -1
						if self.current_pos[i][j][1] <= 0 or self.current_pos[i][j][1] >= self.height:
							self.current_pos[i][j][1] *= -1;
					elif self.current_pos[i][j][0] != self.current_pos[i][j][5] or self.current_pos[i][j][1] != self.current_pos[i][j][6]:
						diffx = (self.current_pos[i][j][5]-self.current_pos[i][j][0])*0.2;
						diffy = (self.current_pos[i][j][6]-self.current_pos[i][j][1])*0.2;
						
						if abs(diffx) < 0.5:
							self.current_pos[i][j][0] = self.current_pos[i][j][5]
						else:
							self.current_pos[i][j][0] += diffx;
						
						if abs(diffy) < 0.5:
							self.current_pos[i][j][1] = self.current_pos[i][j][6]
						else:
							self.current_pos[i][j][1] += diffy;

					else:
						self.current_pos[i][j][4] = 0
					
					posx = ox + self.current_pos[i][j][0]
					posy = oy + self.current_pos[i][j][1]
					drawTexturedRectangle(texture=self.player.texture.get_region(i*self.tx, j*self.ty, self.tx,self.ty), 
						pos=( posx, posy), 
						size=(self.tx,self.ty))
	

	def on_touch_down(self, touch):
		x1 = (self.width - self.player.width) / 2
		x2 = (self.width - self.player.width) / 2 + self.player.width
		y1 = (self.height - self.player.height) / 2
		y2 = (self.height - self.player.height) / 2 + self.player.height
		if touch.x > x1 and touch.x < x2 and touch.y > y1 and touch.y < y2:
			x = touch.x - (self.width - self.player.width) / 2
			y = touch.y - (self.height - self.player.height) / 2
			for i in range(20):
				for j in range(20):
					xdiff = self.current_pos[i][j][0] - x;
					ydiff = self.current_pos[i][j][1] - y;
					dist = sqrt(xdiff*xdiff + ydiff*ydiff);
		            
					randRange = 220+(random()*30);
					rangex = randRange-dist;
					force = 3*(rangex/randRange);
					radians = atan2(ydiff, xdiff);
					self.current_pos[i][j][2] = cos(radians)*force;
					self.current_pos[i][j][3] = sin(radians)*force;
					self.current_pos[i][j][4] = force
		
		
def pymt_plugin_activate(w, ctx):

	if len(sys.argv) < 2:
		print "need a video file as the command line parameter (try super-fly.avi from pymt examples)"
		exit(0)

	bg = VideoExploder(filename=sys.argv[1], size=w.size)
	w.add_widget(bg)
	
def pymt_plugin_deactivate(w, ctx):
	w.children = []
	
#so you can run it as a standalone app
if __name__ == '__main__':
	w = MTWindow()
	ctx = MTContext()
	pymt_plugin_activate(w, ctx)
	runTouchApp()
	pymt_plugin_deactivate(w, ctx)
