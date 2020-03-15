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

	def move_visual(self):
		new_time = self.rect.pos[0] / self.visual_audio_rate
		self.playHead_time = new_time

class SoundVisualizer(Widget):
	speed = NumericProperty(0)

	def update_playhead(self, dt):
		# Move the playhead
		sound_time = self.audioToPlay.get_pos()
		self.pH.playHead_time = sound_time
		self.pH.move()

		# Handle scrolling
		# Step 1. set intitial interpolation value
		if self.hasPaused:
			self.initial_scroll_at_play = self.parent.scroll_x
			self.initial_song_time = self.initial_scroll_at_play * self.pH.song_length
			self.scroll_offset = sound_time / self.pH.song_length - self.initial_scroll_at_play
			self.hasPaused = False

		# Step 2. Calculate scroll velocity
		range_scrollspace = 1.0 - self.initial_scroll_at_play  # 1.0 is end point in scroll space
		range_song_space = self.pH.song_length - self.initial_song_time
		scroll_velocity = range_scrollspace/range_song_space

		#Step 3. Calculate current scroll_x
		self.parent.scroll_x = scroll_velocity * sound_time - self.scroll_offset

	def __init__(self,
				audioVisualSegment,
				audioSound,
				BARS = 5000,
				BAR_HEIGHT = 300,
				BAR_WIDTH = 10,
				LINE_WIDTH = 1,
				**kwargs):
		super(SoundVisualizer, self).__init__(**kwargs)
		self.audioVizData = audioVisualSegment
		self.audioToPlay = audioSound
		self.data = np.fromstring(self.audioVizData._data, np.int16)

		self.scroll_offset = 0.0
		self.hasPaused = False
		self.initial_scroll_at_play = 0.0
		self.initial_song_time = 0.0

		# Set some intitial values
		self.BARS = BARS  #One bar per second
		self.BAR_HEIGHT = BAR_HEIGHT
		self.BAR_WIDTH = BAR_WIDTH
		self.LINE_WIDTH = LINE_WIDTH

		## set widget sizes and size hint
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
				SBar = SoundBar(self.current_x, y_coord, item_height, self.BAR_WIDTH)
				self.bars_on_canvas[i] = (SBar)
				self.add_widget(SBar, 1)
			self.current_x = self.current_x + self.LINE_WIDTH + self.BAR_WIDTH

		with self.canvas:
			self.pH = PlayHead(len(self.audioVizData)/1000,len(self.max_array) * (self.LINE_WIDTH + self.BAR_WIDTH), 1)
			self.add_widget(self.pH)

	def schedule_animation(self, sound):
		event = Clock.schedule_interval(self.update_playhead, 1 / 60. )#/ 30.)

	def unSchedule_animation(self, sound):
		Clock.unschedule(self.update_playhead)
		self.hasPaused = True

	def on_touch_down(self, touch):
		print("in widget")
		if touch.y > self.pH.rect.pos[1]:
			with self.canvas:
				Color(1, 0, 0)
				#Rectangle(pos = touch.pos, size = (10, 10))
			self.pH.rect.pos = (touch.pos[0], self.pH.rect.pos[1])
			self.pH.move_visual()

			print("Touch y: {} below: {}".format(touch.y, self.pH.rect.pos[1]))
		super(SoundVisualizer, self).on_touch_down(touch)


class ScrollableSoundVizualizer(ScrollView):

	def __init__(self, audioViz, sound,**kwargs):
		super(ScrollableSoundVizualizer, self).__init__(**kwargs)
		self.visualizer = SoundVisualizer(audioViz, sound)
		self.visualizer.preprocess_data()
		self.visualizer.start(1, 300.0)
		self.add_widget(self.visualizer, 0)
		self.size_hint_x = None
		self.size = Window.size
		self.do_scroll_x = True
		self.scroll_type = ['content','bars']

		sound.bind(on_play = self.visualizer.schedule_animation)
		sound.bind(on_stop = self.visualizer.unSchedule_animation)

class SoundVisualizerApp(App):
	def build(self):

		#Read and parse audio data
		src= "./AdhesiveWombat - Anthem.mp3"#"./test.mp3"
		audio = AudioSegment.from_file(src)
		self.sound = SoundLoader.load(src)
		sView = ScrollableSoundVizualizer(audio, self.sound)

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
				app = App.get_running_app()
				self.sound_pos = app.root.visualizer.pH.playHead_time
				print("sound_pos {}".format(self.sound_pos))
				self.sound.play()
				if self.sound_pos < self.sound.length:
					self.sound.seek(self.sound_pos)
			else:
				self.sound.stop()
		return True


if __name__ == '__main__':
	SoundVisualizerApp().run()
