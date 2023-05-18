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
import sys
import wave
from pathlib import Path

import pyaudio
from PySide6.QtCore import QCoreApplication, QObject, Signal

log = logging.getLogger(__name__)


class AudioProcessor(QObject):
    '''Thread-safe object for recording audio.'''
    finished = Signal()

    def __init__(self, audio_path: Path = None, input_device_index: int = 0) -> None:
        super().__init__()
        self.exc: Exception = None
        self.audio_path = audio_path
        self.audio_file = None
        self.input_device_index = input_device_index
        self._keep_processing: bool = False
        self._start_recording: bool = False
        self._chunk = 1024
        self._format = pyaudio.paInt16
        self._channels = 1 if sys.platform == 'darwin' else 2
        self._rate = 44100

    def on_new_name(self, new_name: Path):
        '''New name for the recorded file is available.'''
        log.debug(f'New recording name available: {new_name}')
        self.audio_path = new_name.with_suffix('.wav')
        log.debug(f'New audio file path is: {self.audio_path}')

    def run(self):
        '''Prepare audio stream for recording.'''
        try:
            self._process()
        except Exception as exc:
            log.critical('An unhandled exception occurred while running AudioProcessor._process()!')
            log.critical('Exception details follow:')
            log.critical(exc)
            self.exc = exc

    def start(self):
        '''Start recording audio stream.'''
        log.info('Starting audio recording.')
        self._start_recording = True

    def stop(self):
        '''Stop recording audio stream.'''
        log.info('Stopping audio recording.')
        self._keep_processing = False

    def _process(self):
        self._keep_processing = True
        log.info('Initializing audio processor.')
        is_recorded = False
        while self.audio_path is None:
            # Wait for audio filename to be set
            QCoreApplication.processEvents()
        with wave.open(str(self.audio_path), 'wb') as self.audio_file:
            audio = pyaudio.PyAudio()
            self.audio_file.setnchannels(self._channels)
            self.audio_file.setsampwidth(audio.get_sample_size(self._format))
            self.audio_file.setframerate(self._rate)
            stream = audio.open(format=self._format,
                                channels=self._channels,
                                rate=self._rate,
                                input=True,
                                input_device_index=self.input_device_index,
                                start=False,
                                stream_callback=self._callback)
            log.info('Audio processor initialized. Waiting for start signal.')
            while not self._start_recording and self._keep_processing:
                # Breathe, dawg
                QCoreApplication.processEvents()
            if self._keep_processing:
                stream.start_stream()
                log.info(f'Recording audio to {self.audio_path}')
                while stream.is_active() and self._keep_processing:
                    # Breathe, dawg
                    QCoreApplication.processEvents()
                is_recorded = True
                log.info('Finished recording audio.')
            else:
                log.info('Quitting audio processor before start of recording.')
        stream.stop_stream()
        stream.close()
        audio.terminate()
        if not is_recorded:
            print(f'deleting audio file `{self.audio_path}`')
            log.info(f'Deleting empty audio file `{self.audio_path}`')
            self.audio_path.unlink(missing_ok=False)
        log.info('Exiting audio processor.')
        self.finished.emit()

    def _callback(self, in_data, frame_count, time_info, status):
        '''For async audio recording. See pyaudio docs.'''
        self.audio_file.writeframes(in_data)
        return (in_data, pyaudio.paContinue)
