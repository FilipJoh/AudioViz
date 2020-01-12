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
from kivy.graphics import Color
from kivy.properties import NumericProperty
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.uix.scrollview import ScrollView
from kivy.config import Config


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

	def __init__(self, current_x, current_y, scale_y,width, **kwargs):
		super(SoundBar, self).__init__(**kwargs)
		with self.canvas:
			self.rect = Rectangle(pos = (current_x, current_y), size = (width,scale_y))
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
			Color(1.,0.,0.)
			self.rect = Rectangle(pos = (start_x, 100.0), size = (1, 400))
		self.visual_audio_rate = song_visual_width/song_length  #Should be the playrate
		self.song_length = song_length
		self.song_visual_width = song_visual_width
		self.start_x = start_x

	def move(self):
		newPos_x = self.playHead_time * self.visual_audio_rate + self.start_x
		self.rect.pos = (newPos_x, 100.0)

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
		self.BAR_WIDTH = 2
		self.LINE_WIDTH = 20
		self.bar_counter = 0
		self.current_bar = 0
		self.current_time_in_song = 0


	def preprocess_data(self):
		length = len(data)
		self.RATIO = length/self.BARS
		count = 0
		maximum_item = 0
		self.max_array = np.zeros(self.BARS)
		highest_line = 0
		index = 0

		datasrc = "./waveform.npy"
		if not os.path.exists(datasrc):
			for d in data:
				if count < self.RATIO:
					count = count + 1

					if abs(d) > maximum_item:
						maximum_item = abs(d)
				else:
					self.max_array[index] = (maximum_item)
					index += 1
					if maximum_item > highest_line:
						highest_line = maximum_item

					maximum_item = 0
					count = 1

			while len(self.max_array) < self.BARS:
				self.max_array[index] = 0
				index += 1

			np.save(datasrc, self.max_array)
		else:
			barData = np.load(datasrc)
			self.max_array = barData
			highest_line = barData.max()
		self.line_ratio = highest_line/self.BAR_HEIGHT

	def start(self, start_x, start_y):
		self.current_x = start_x
		self.current_y = start_y

		self.bars_on_canvas = [None] * self.BARS
		for i in range(self.BARS):
			with self.canvas:
				Color(1.0,1.,1.)
				item_height = self.max_array[i] / self.line_ratio
				y_coord = ( - item_height)/2 + start_y
				self.bars_on_canvas[i] = (SoundBar(self.current_x, y_coord, item_height, self.BAR_WIDTH))
			self.current_x = self.current_x + self.LINE_WIDTH + self.BAR_WIDTH
			self.current_bar += 1

		with self.canvas:
			self.pH = PlayHead(len(audio)/1000,self.BARS * (self.LINE_WIDTH + self.BAR_WIDTH), 1)

	def schedule_animation(self, sound):
		event = Clock.schedule_interval(self.update_playhead, 1 / 30. )#/ 30.)

	def unSchedule_animation(self, sound):
		Clock.unschedule(self.update_playhead)
		print("Song {} of {} played".format(self.current_time_in_song, len(audio)))

class SoundVisualizerApp(App):
	def build(self):
		Config.set('graphics', 'width', '1000')
		Config.set('graphics', 'height', '600')
		sWig = SoundVisualizerWidget(size = (5000 * 2 * 20, 600), size_hint_x = None)
		sWig.set_init_vals()
		sWig.preprocess_data()
		sWig.start(1, 300.0)

		sView = ScrollView(size_hint=(None, 1), size=(1000, 600))
		sView.add_widget(sWig)
		sView.do_scroll_x = True

		sound.bind(on_play = sWig.schedule_animation)
		sound.bind(on_stop = sWig.unSchedule_animation)
		sound.play()
		return sView

if __name__ == '__main__':
	SoundVisualizerApp().run()
