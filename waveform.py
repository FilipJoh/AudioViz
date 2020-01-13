from pydub import AudioSegment

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

import math

import pdb

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
		self.pH.playHead_time = self.audioToPlay.get_pos()
		self.pH.move()

	def __init__(self,
				audioVisualSegment,
				audioSound,
				BARS = 5000,
				BAR_HEIGHT = 300,
				BAR_WIDTH = 1,
				LINE_WIDTH = 0,
				**kwargs):
		super(SoundVisualizerWidget, self).__init__(**kwargs)
		self.audioVizData = audioVisualSegment
		self.audioToPlay = audioSound
		self.data = np.fromstring(self.audioVizData._data, np.int16)

		# Set some intitial values
		self.BARS = BARS  #One bar per second
		self.BAR_HEIGHT = BAR_HEIGHT
		self.BAR_WIDTH = BAR_WIDTH
		self.LINE_WIDTH = LINE_WIDTH

		# set widget sizes and size hint
		self.size = (self.BARS * (self.BAR_WIDTH + self.LINE_WIDTH), 600)
		self.size_hint_x = None

	def _keyboard_closed(self):
		self._keyboard.unbind(on_key_down=self._on_keyboard_down)
		self._keyboard = None

	def preprocess_data(self):
		length = len(self.data)
		self.RATIO = length/self.BARS
		self.RATIO = int(math.ceil(self.RATIO))

		residual = self.RATIO*self.BARS - length
		residual_zeros = np.zeros(residual)
		total_data = np.append(self.data, residual_zeros)

		Bins = np.split(total_data, self.BARS)

		self.max_array = [np.max(arr) for arr in Bins]
		self.line_ratio = np.max(self.max_array)/self.BAR_HEIGHT#highest_line/self.BAR_HEIGHT

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

		with self.canvas:
			self.pH = PlayHead(len(self.audioVizData)/1000,self.BARS * (self.LINE_WIDTH + self.BAR_WIDTH), 1)

	def schedule_animation(self, sound):
		event = Clock.schedule_interval(self.update_playhead, 1 / 30. )#/ 30.)

	def unSchedule_animation(self, sound):
		Clock.unschedule(self.update_playhead)

class SoundVisualizerApp(App):
	def build(self):
		# Set WindowSize
		Config.set('graphics', 'width', '1000')
		Config.set('graphics', 'height', '600')

		#Read and parse audio data
		src= "./AdhesiveWombat - Anthem.mp3"#"./test.mp3"
		audio = AudioSegment.from_file(src)
		self.sound = SoundLoader.load(src)

		sWig = SoundVisualizerWidget(audio, self.sound)
		sWig.preprocess_data()
		sWig.start(1, 300.0)

		sView = ScrollView(size_hint=(None, 1), size=(1000, 600))
		sView.add_widget(sWig)
		sView.do_scroll_x = True

		self.sound.bind(on_play = sWig.schedule_animation)
		self.sound.bind(on_stop = sWig.unSchedule_animation)
		self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
		self._keyboard.bind(on_key_down = self._on_keyboard_toggle)

		self.sound_pos = 0
		return sView

	def _keyboard_closed(self):
		self._keyboard.unbind(on_key_down=self._on_keyboard_toggle)
		self._keyboard = None

	def _on_keyboard_toggle(self, keyboard, keycode, text, modifiers):
		#pdb.set_trace()
		if keycode[1] == 'spacebar':
			if self.sound.state == 'stop':
				self.sound.play()
				if self.sound_pos < self.sound.length:
					self.sound.seek(self.sound_pos)
			else:
				self.sound_pos = self.sound.get_pos()
				self.sound.stop()
		return True


if __name__ == '__main__':
	SoundVisualizerApp().run()
