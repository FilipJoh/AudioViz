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
Window.size = (1000, 600)

from pydub.playback import play
import pdb

src= "./test.mp3"
"""audio = 0
for i in range(10):
	audio += generators.Sine(freq=440).to_audio_segment(duration=1000.0)
	audio += AudioSegment.silent(duration=1000)
audio.export(src)"""
audio = AudioSegment.from_file(src)

sound = SoundLoader.load(src)
data = np.fromstring(audio._data, np.int16)

class SoundBar(Widget):
	setable_size_y = NumericProperty(0)
	setable_pos_y = NumericProperty(0)

	def __init__(self, current_x, current_y, scale_y, **kwargs):
		super(SoundBar, self).__init__(**kwargs)
		with self.canvas:
			self.rect = Rectangle(pos = (current_x, current_y), size = (1,scale_y))
			self.current_x = current_x

	def scale(self):
		self.rect.size = (1, self.setable_size_y)

	def move_y(self):
		self.rect.pos = (self.current_x, self.setable_pos_y)

class PlayHead(Widget):
	playHead_time = NumericProperty(0)

	def __init__(self, song_length, song_visual_width, start_x, **kwargs):
		super(PlayHead, self).__init__(**kwargs)
		with self.canvas:
			self.rect = Rectangle(pos = (start_x, 200.0), size = (1, 600))
		self.visual_audio_rate = song_visual_width/song_length  #Should be the playrate
		self.song_length = song_length
		self.song_visual_width = song_visual_width
		self.start_x = start_x

	def move(self):
		newPos_x = self.playHead_time * self.visual_audio_rate + self.start_x
		self.rect.pos = (newPos_x, 00.0)
		print("head at {}/{} in time, {}/{} in animation".format(self.playHead_time, self.song_length, self.playHead_time * self.visual_audio_rate, self.song_visual_width))

class SoundVisualizerWidget(Widget):
	speed = NumericProperty(0)

	def update_playhead(self, dt):
		self.pH.playHead_time = sound.get_pos()
		self.pH.move()

	def __init__(self, **kwargs):
		super(SoundVisualizerWidget, self).__init__(**kwargs)

	def _keyboard_closed(self):
		self._keyboard.unbind(on_key_down=self._on_keyboard_down)
		self._keyboard = None

	def set_init_vals(self):
		self.BARS = 5000  #One bar per second
		self.BAR_HEIGHT = 300
		self.LINE_WIDTH = 1
		self.bar_counter = 0
		self.current_bar = 0
		self.current_time_in_song = 0
		with self.canvas:
			self.pH = PlayHead(len(audio)/1000,self.BARS * (self.LINE_WIDTH), 1)

	def preprocess_data(self):
		length = len(data)
		self.RATIO = length/self.BARS
		count = 0
		maximum_item = 0
		self.max_array = []
		highest_line = 0

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

		while len(self.max_array) < self.BARS:
			self.max_array.append(0)

		self.line_ratio = highest_line/self.BAR_HEIGHT

	def start(self, start_x, start_y):
		self.current_x = start_x
		self.current_y = start_y

		self.bars_on_canvas = []
		for i in range(self.BARS):
			with self.canvas:
				item_height = self.max_array[i] / self.line_ratio
				y_coord = (self.BAR_HEIGHT - item_height)/2 + self.current_y
				self.bars_on_canvas.append(SoundBar(self.current_x, y_coord, item_height))
			self.current_x = self.current_x + self.LINE_WIDTH
			self.current_bar += 1

	def schedule_animation(self, sound):
		event = Clock.schedule_interval(self.update_playhead, 1 / 30. )#/ 30.)

	def unSchedule_animation(self, sound):
		Clock.unschedule(self.update_playhead)
		print("Song {} of {} played".format(self.current_time_in_song, len(audio)))

	def update_all_bars(self, dt):

		for barIndex in range(len(self.bars_on_canvas)):
			bar = self.bars_on_canvas[barIndex]
			if (self.current_time_in_song + len(self.bars_on_canvas)) < len(self.max_array):
				item_height = self.max_array[self.current_time_in_song + barIndex]/self.line_ratio
				#with self.canvas:
				current_y = (self.BAR_HEIGHT - item_height)/2 + self.current_y
				bar.setable_size_y = item_height.item()
				bar.setable_pos_y = (current_y-250).item()
				bar.scale()
				bar.move_y()

		self.current_time_in_song += int(self.speed)#+ fs/10)
		#self.empty_bars -= int(self.speed)#+ fs/10)
		if self.current_time_in_song > len(self.max_array) - 1:
			self.current_time_in_song = 0
			Clock.unschedule(self.update_all_bars)


class SoundVisualizerApp(App):
	def build(self):
		sWig = SoundVisualizerWidget()
		sWig.set_init_vals()
		sWig.preprocess_data()
		sWig.start(1, 300.0)
		sound.bind(on_play = sWig.schedule_animation)
		sound.bind(on_stop = sWig.unSchedule_animation)
		sound.play()
		return sWig

if __name__ == '__main__':
	SoundVisualizerApp().run()
