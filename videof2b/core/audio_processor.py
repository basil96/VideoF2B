# -*- coding: utf-8 -*-
# VideoF2B - Draw F2B figures from video
# Copyright (C) 2023  Andrey Vasilik - basil96
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

'''
The audio processor in VideoF2B.  Used during capture of live video.
'''

import logging
from pathlib import Path
import sys
import wave

import pyaudio
from PySide6.QtCore import QCoreApplication, QObject, Signal

log = logging.getLogger(__name__)


class AudioProcessor(QObject):
    def __init__(self, audio_path: Path, input_device_index=None) -> None:
        super().__init__()
        self.audio_path = audio_path
        self._input_device_index = input_device_index
        self._keep_processing: bool = False
        self._chunk = 1024
        self._format = pyaudio.paInt16
        self._channels = 1 if sys.platform == 'darwin' else 2
        self._rate = 44100
        self._recording_time = 5

    def start(self):
        self._keep_processing = True
        log.info('Starting audio recording.')
        with wave.open(self.audio_path, 'wb') as audio_file:
            audio = pyaudio.PyAudio()
            audio_file.setnchannels(self._channels)
            audio_file.setsampwidth(audio.get_sample_size(self._format))
            audio_file.setframerate(self._rate)
            stream = audio.open(format=self._format,
                                channels=self._channels,
                                rate=self._rate,
                                input=True,
                                input_device_index=self._input_device_index)
            log.info('Recording audio')
            for _ in range(0, self._rate // self._chunk * self._recording_time):
                audio_file.writeframes(stream.read(self._chunk))
            log.info('Finished recording audio.')
            stream.close()
            audio.terminate()

    def stop(self):
        self._keep_processing = False
