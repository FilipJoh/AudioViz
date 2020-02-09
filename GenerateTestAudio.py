from pydub import AudioSegment
from pydub import generators

#
#   Small Script to generate test audio
#

src= "./test.mp3"
audio = 0
for i in range(100):
	audio += generators.Sine(freq=440).to_audio_segment(duration=1000.0)
	audio += AudioSegment.silent(duration=1000)
audio.export(src)
