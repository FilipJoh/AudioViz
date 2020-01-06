from pydub import AudioSegment
from pydub import generators
from matplotlib import pyplot as plt
from PIL import Image, ImageDraw
import numpy as np
import os
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Rectangle
from kivy.properties import NumericProperty
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
Window.size = (1000, 800)

from pydub.playback import play
import pdb

#src = "./test.mp3"
src= "./testy.wav"
#pdb.set_trace()
#audio = AudioSegment.from_file(src)
audio = 0#AudioSegment.silent(duration=1000)
for i in range(10):
	audio += generators.Sine(freq=440).to_audio_segment(duration=1000.0)
	audio += AudioSegment.silent(duration=1000)
audio.export(src)
#audio = audio[0:10000]
sound = SoundLoader.load(src)
data = np.fromstring(audio._data, np.int16)
fs = audio.frame_rate
#pdb.set_trace()

class SoundBar(Widget):
	setable_size_y = NumericProperty(0)
	setable_pos_y = NumericProperty(0)

	def __init__(self, current_x, current_y, scale_y, **kwargs):
		super(SoundBar, self).__init__(**kwargs)
		with self.canvas:
			self.rect = Rectangle(pos = (current_x, current_y), size = (1,scale_y))
			self.current_x = current_x

	def scale(self):
		self.rect.size = (4, self.setable_size_y)

	def move_y(self):
		self.rect.pos = (self.current_x, self.setable_pos_y)

class SoundVisualizerWidget(Widget):
	speed = NumericProperty(0)


	def __init__(self, **kwargs):
		super(SoundVisualizerWidget, self).__init__(**kwargs)
		self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
		self._keyboard.bind(on_key_down=self._on_keyboard_down)
		self.speed = 1#1#33.8#int(fs/1000/2)#fs/30/2

	def _keyboard_closed(self):
		self._keyboard.unbind(on_key_down=self._on_keyboard_down)
		self._keyboard = None

	def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
		if keycode[1] == 'w':
			self.speed += 1
		elif keycode[1] == 's':
			self.speed -= 1
		elif keycode[1] == 'up':
			self.speed += 1
		elif keycode[1] == 'down':
			self.speed -= 1
		return True



	def set_init_vals(self):
		self.BARS = int(len(audio)/1000)  #One bar per second
		#pdb.set_trace()
		self.BAR_HEIGHT = 300
		self.LINE_WIDTH = 20
		self.BARS_ON_SCREEN = 20
		self.bar_counter = 0
		self.current_bar = 0
		self.current_time_in_song = 0


	def preprocess_data(self):
		length = len(data)
		self.RATIO = length/self.BARS
		#pdb.set_trace()
		count = 0
		maximum_item = 0
		self.max_array = []
		highest_line = 0

		self.empty_bars = int(self.BARS_ON_SCREEN/2)-1
		for i in range(self.empty_bars):
			self.max_array.append(20)

		for d in data:
			if count < self.RATIO:
				count = count + 1

				if abs(d) > maximum_item:
					maximum_item = abs(d)
			else:
				self.max_array.append(maximum_item)

				if maximum_item > highest_line:
					highest_line = maximum_item

				maximum_item = 0
				count = 1
		#pdb.set_trace()

		for i in range(self.empty_bars):
			self.max_array.append(20)

		self.line_ratio = highest_line/self.BAR_HEIGHT

	def start(self, start_x, start_y):
		self.current_x = start_x
		self.current_y = start_y

		self.bars_on_canvas = []
		for i in range(self.BARS_ON_SCREEN):
			#self.bar_counter += 1
			#current_y = (self.BAR_HEIGHT - item_height)/2 + touch.y
			with self.canvas:
				self.bars_on_canvas.append(SoundBar(self.current_x, self.current_y-250, 120))

			#for rect in self.bars_on_canvas:
			#	rect.bind(size self.update_size)
			self.current_x = self.current_x + self.LINE_WIDTH
			self.current_bar += 1
			#self.current_time_in_song += 1
		self.empty_bars = int(self.BARS_ON_SCREEN/2)

		with self.canvas:
			Rectangle(pos = (498,0), size = (2,800) )

		#event = Clock.schedule_interval(self.update_all_bars, 1 / 30.)

	def schedule_animation(self, sound):
		event = Clock.schedule_interval(self.update_all_bars, 1 / 2. )#/ 30.)

	def unSchedule_animation(self, sound):
		Clock.unschedule(self.update_all_bars)
		print("Song {} of {} played".format(self.current_time_in_song, len(audio)))

	def update_all_bars(self, dt):

		for barIndex in range(len(self.bars_on_canvas)):
			bar = self.bars_on_canvas[barIndex]
			#pdb.set_trace()

			#if (barIndex > self.empty_bars):
				#print("barIndex {}".format(barIndex))
			if (self.current_time_in_song + len(self.bars_on_canvas)) < len(self.max_array):
				item_height = self.max_array[self.current_time_in_song + barIndex]/self.line_ratio
				#with self.canvas:
				current_y = (self.BAR_HEIGHT - item_height)/2 + self.current_y
				bar.setable_size_y = item_height.item()
				bar.setable_pos_y = (current_y-250).item()
				bar.scale()
				bar.move_y()

		self.current_time_in_song += int(self.speed)#+ fs/10)
		self.empty_bars -= int(self.speed)#+ fs/10)
		if self.current_time_in_song > len(self.max_array) - 1:
		#	self.current_time_in_song += 1 #len(self.bars_on_canvas)
		#else:
			pdb.set_trace()
			self.current_time_in_song = 0
			Clock.unschedule(self.update_all_bars)

			#self.empty_bars = 100000
		#print("speed {}, empty_bars {}, current_time_in_song {}".format(self.speed, self.empty_bars, self.current_time_in_song))

	def update_bars(self, dt):
		#print('Callback called, delta: {}'.format(dt))
		#print('')
		#pdb.set_trace()
		if self.current_bar < (self.BARS_ON_SCREEN - 1):
			self.current_bar += 1
		else:
			self.current_bar = 0
		self.bar_counter += 1
		"""if self.bar_counter < self.BARS_ON_SCREEN and self.current_bar < self.BARS_ON_SCREEN:
			item_height = self.max_array[self.bar_counter] / self.line_ratio
			current_y = (self.BAR_HEIGHT - item_height)/2 + self.current_y
			with self.canvas:
				#Rectangle(pos = (self.current_x, current_y), size = (4, item_height))
				self.bars_on_canvas.append(SoundBar(self.current_x, self.current_y, item_height))
			self.current_x = self.current_x + self.LINE_WIDTH
			#print('Draw new rectangle')
			#for rect in self.bars_on_canvas:
			#	rect.bind(size self.update_size)
		else:"""

		item_height = self.max_array[self.current_time_in_song] / self.line_ratio
			#pdb.set_trace()
			#print('update_rectangle {} with scale: {}, converted {}\n'.format(self.current_bar, item_height,item_height.item()))
		#pdb.set_trace()
		self.bars_on_canvas[self.current_bar].setable_size_y = item_height.item()
		self.bars_on_canvas[self.current_bar].scale()
		"""for barIndex in range(len(self.bars_on_canvas)):
			bar = self.bars_on_canvas[barIndex]
			if self.bar_counter + len(self.bars_on_canvas) < len(self.max_array):
				item_height = self.max_array[barIndex]/self.line_ratio
				with self.canvas:
					bar = Rectangle(pos = bar.pos, size=(4, item_height))"""
		if self.current_time_in_song < len(self.max_array) - 1:
			self.current_time_in_song += 1
		else:
			self.current_time_in_song = 0








class SoundVisualizerApp(App):
	def build(self):
		sWig = SoundVisualizerWidget()
		sWig.set_init_vals()
		sWig.preprocess_data()
		sWig.start(500-sWig.BARS/2 * (sWig.LINE_WIDTH +4), 400.0)
		sound.bind(on_play = sWig.schedule_animation)
		sound.bind(on_stop = sWig.unSchedule_animation)
		sound.play()
		return sWig

	"""def ahuba(self, sound):
		self.sWig.schedule_animation()"""

if __name__ == '__main__':
	SoundVisualizerApp().run()

#im.show()
