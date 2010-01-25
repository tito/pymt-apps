# PYMT Plugin integration
IS_PYMT_PLUGIN = True
PLUGIN_TITLE = 'Musicrow'
PLUGIN_AUTHOR = 'Remi Pauchet'
PLUGIN_DESCRIPTION = 'Play!'

'''
TODO:

x other scales, harmonic minor, etc...
- drumkit
x game of life
x tempo+/-
x transpose up/down
- light effects
- multitrack
- update bpm slider on preset load
- move event
'''

from pymt import *


class World(MTWidget):
	def __init__(self, **kwargs):
		super(World, self).__init__(**kwargs)
		
		self.bpm = 180
		self.game_of_life = False
		self.paused = False
		self.reset()
		
		# load a music scale
		self.sound = []
		self.load_kalimba() #by default
		
		self.create_menu()
		
		#go for it !
		getClock().schedule_interval(self.play, 60.0/self.bpm)

	def load_kalimba(self, *largs):
		#pause ?
		self.sound = []
		for i in range(16):
			soundfile = "sound/kalimba/kalimba%s.ogg" % (i+1)
			self.sound.append(SoundLoader.load(soundfile))

	def load_oud(self, *largs):
		#pause ?
		self.sound = []
		scale = ('B1', 'C2', 'C#2', 'E2', 'F2', 'G2', 'G#2', 'B2', 'C3', 'C#3', 'E3', 'F3', 'G3', 'G#3', 'B3', 'C4')
		for i in scale:
			soundfile = "sound/oud/oud_%s.ogg" % (i)
			self.sound.append(SoundLoader.load(soundfile))

	def create_menu(self):
		xml = '''<?xml version="1.0" encoding="UTF-8"?>
		<MTBoxLayout id="'menu'" orientation="'vertical'" invert_y="True">
		 <MTGridLayout cols="2">
		  <MTLabel label="'Bpm:'" size="(120, 30)"/>
		  <MTSlider id="'slider_tempo'" min="50" max="300" value="180" orientation="'horizontal'" value_show="True" size="(200, 30)"/>
		 </MTGridLayout>
		 <MTGridLayout cols="3">
		  <MTLabel label="'Instrument:'" size="(120, 30)"/>
          <MTButton id="'button_kalimba'" label="'Kalimba'" size="(100, 30)"/>
          <MTButton id="'button_oud'" label="'Oud'" size="(100, 30)"/>
		 </MTGridLayout>
		 <MTGridLayout cols="3">
		  <MTLabel label="'Transpose:'" size="(120, 30)"/>
		  <MTButton id="'button_transpose_up'" label="'Up'" size="(100, 30)"/>
		  <MTButton id="'button_transpose_down'" label="'Down'" size="(100, 30)"/>
		 </MTGridLayout>
		 <MTGridLayout cols="3">
		  <MTButton id="'button_clear'" label="'Clear'" size="(100, 30)"/>
		  <MTButton id="'button_pause'" label="'Pause'" size="(100, 30)"/>
		  <MTButton id="'button_game_of_life'" label="'Game of life'" size="(100, 30)"/>
		 </MTGridLayout>
		 <MTGridLayout cols="6">
		  <MTLabel label="'Preset:'" size="(120, 30)"/>
		  <MTButton id="'button_preset1'" label="'Offspring'" size="(100, 30)"/>
		  <MTButton id="'button_preset2'" label="'Close Encounters'" size="(120, 30)"/>
		  <MTButton id="'button_preset3'" label="'Oscillator1'" size="(120, 30)"/>
		  <MTButton id="'button_preset5'" label="'Oscillator2'" size="(120, 30)"/>
		  <MTButton id="'button_preset4'" label="'spaceship'" size="(120, 30)"/>
		 </MTGridLayout>
		</MTBoxLayout>
		'''

		w = XMLWidget()
		w.loadString(xml)

		layout = getWidgetById('menu')
		corner = MTSidePanel(layout=layout)
		self.add_widget(corner)
		getWidgetById('slider_tempo').connect('on_value_change', self.update_bpm)
		getWidgetById('button_kalimba').connect('on_press', self.load_kalimba)
		getWidgetById('button_oud').connect('on_press', self.load_oud)
		getWidgetById('button_clear').connect('on_press', self.reset)
		getWidgetById('button_pause').connect('on_press', self.toggle_pause)
		getWidgetById('button_game_of_life').connect('on_press', self.toggle_game_of_life)
		getWidgetById('button_transpose_up').connect('on_press', self.transpose_up)
		getWidgetById('button_transpose_down').connect('on_press', self.transpose_down)
		getWidgetById('button_preset1').connect('on_press', self.preset1)
		getWidgetById('button_preset2').connect('on_press', self.preset2)
		getWidgetById('button_preset3').connect('on_press', self.preset3)
		getWidgetById('button_preset4').connect('on_press', self.preset4)
		getWidgetById('button_preset5').connect('on_press', self.preset5)
		
	def reset(self, *largs):
		self.gridx = 16
		self.gridy = 16
		self.grid = [[0 for i in range(self.gridx)] for i in range(self.gridy)]
		self.stepx = 1;
		self.stepy = 1;
		self.currentrow = 0;


	def on_touch_down(self, touch):
		
		#other widgets
		if super(World, self).on_touch_down(touch):
			return True
		
		for x in range(self.gridx):
			#find x pad
			if (touch.x >= (2+x)*self.stepx -10) and (touch.x <= (2+x)*self.stepx +10):
				for y in range(self.gridy):
					#find y pad
					if (touch.y >= (2+y)*self.stepy -10) and (touch.y <= (2+y)*self.stepy +10):
						self.grid[x][y] = 1 - self.grid[x][y]
						return 1
		return 0
	
	
	def play(self,dt):
		#we move
		if self.currentrow < self.gridx - 1:
			self.currentrow += 1
		else:
			self.currentrow = 0
			#cellular evolution ?
			if self.game_of_life:
				self.process_game_of_life()
		#we play
		for i in range(self.gridy ):
			if self.grid[self.currentrow][i] == 1:
				self.sound[i].stop()
				self.sound[i].play()

		
	def draw(self):
		
		w = self.get_parent_window()
		
		self.stepx = w.width / (self.gridx + 4)
		self.stepy = w.height / (self.gridy + 4)
		
		#draw pads
		for x in range(self.gridx):
			for y in range(self.gridy):
				if self.grid[x][y] == 1:
					set_color(0.6,1,0.6, 1) #pushed
				else:
					set_color(0.98,0.98,0.89, 1) #free
				drawCircle( ((2+x)*self.stepx  ,(2+y)*self.stepy), 20)
		
		#draw row played
		set_color(1, 0, 0, .5)
		drawRectangle( ((2+self.currentrow)*self.stepx-20 ,2*self.stepy-20), (40,self.gridy *self.stepy ))

	def toggle_pause(self, *largs):
		if self.paused:
			self.paused = False
			getClock().schedule_interval(self.play, 60.0/self.bpm)
		else:
			self.paused = True
			getClock().unschedule(self.play)

	def toggle_game_of_life(self, *largs):
		if self.game_of_life:
			self.game_of_life = False
		else:
			self.game_of_life = True

	def process_game_of_life(self):
		
		#copy the original grid
		original_grid= [[0 for i in range(self.gridx)] for i in range(self.gridy)]
		for x in range(self.gridx):
			for y in range(self.gridy):
				original_grid[x][y] = self.grid[x][y]
		'''
		1 2 3
		4 X 5
		6 7 8
		'''
		def count_neighbour(x,y):
			count = 0
			#1
			if x>0 and y+1<self.gridy and original_grid[x-1][y+1] == 1:
				count +=1
			#2
			if y+1< self.gridy and original_grid[x][y+1] == 1:
				count +=1
			#3
			if x+1< self.gridx and y+1< self.gridy and original_grid[x+1][y+1] == 1:
				count +=1
			#4
			if x>0 and original_grid[x-1][y] == 1:
				count +=1
			#5
			if x+1< self.gridx and original_grid[x+1][y] == 1:
				count +=1
			#6
			if x>0 and y-1>0 and original_grid[x-1][y-1] == 1:
				count +=1
			#7
			if y-1>0 and original_grid[x][y-1] == 1:
				count +=1
			#8
			if x+1<self.gridx and y-1>0 and original_grid[x+1][y-1] == 1:
				count +=1
			return count

		for x in range(self.gridx):
			for y in range(self.gridy):
				count = count_neighbour(x,y)
				#3 neighbours -> alive
				if count == 3:
					self.grid[x][y] = 1
				#2 neighbours -> same state
				elif count == 2:
					pass
				#dead
				else:
					self.grid[x][y] = 0

	#move cells up
	def transpose_up(self, *largs):
		for x in range(self.gridx):
			save = self.grid[x][self.gridy-1]
			for y in range(self.gridy-1,0,-1):
				self.grid[x][y] = self.grid[x][y-1]
			self.grid[x][0] = save
	
	#move cells down
	def transpose_down(self, *largs):
		for x in range(self.gridx):
			save = self.grid[x][0]
			for y in range(self.gridy-1):
				self.grid[x][y] = self.grid[x][y+1]
			self.grid[x][self.gridy-1] = save

	#change tempo
	def update_bpm(self, bpm):
		self.bpm = bpm
		getClock().unschedule(self.play)
		getClock().schedule_interval(self.play, 60.0/self.bpm)


	
	def load_preset(self, preset):
		
		namespace = dict()
		execfile('preset/'+preset+'.py',namespace)
		
		self.reset()
		
		y = self.gridy - 1
		for line in namespace['motif'].split('\n'):
			if line == "":
				continue
			for x in range(self.gridx):
				if line[x] == '1':
					self.grid[x][y] = 1
			y -= 1

		if 'instrument' in namespace:
			if namespace['instrument'] == 'kalimba':
				self.load_kalimba();
			if namespace['instrument'] == 'oud':
				self.load_oud();			
		if 'bpm' in namespace:
			self.update_bpm(namespace['bpm'])
		if 'game_of_life' in namespace:
			self.game_of_life = namespace['game_of_life']
		
		
	#can't remember the name - The Offspring
	def preset1(self, *largs):
		self.load_preset('offspring')
		
	#Close Encounters of the Third Kind - theme
	def preset2(self, *largs):
		self.load_preset('encounter')
		
	#game of life oscillator
	def preset3(self, *largs):
		self.load_preset('oscillator1')
		
	#game of life space ship
	def preset4(self, *largs):
		self.load_preset('spaceship')

	#flower
	def preset5(self, *largs):
		self.load_preset('oscillator2')

def pymt_plugin_activate(w, ctx):
	ctx.c = World()
	w.add_widget(ctx.c)
	#bg = MTSvg(filename="fond.svg")
	#w.add_widget(bg)

def pymt_plugin_deactivate(w, ctx):
	w.remove_widget(ctx.c)

if __name__ == '__main__':
	w = MTWindow( )
	ctx = MTContext()
	pymt_plugin_activate(w, ctx)
	runTouchApp()
	pymt_plugin_deactivate(w, ctx)
