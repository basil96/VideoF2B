# -*- coding: utf-8 -*-
# VideoF2B - Draw F2B figures from video
# Copyright (C) 2021  Andrey Vasilik - basil96@users.noreply.github.com
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
Discovers and enumerates available devices on the system.
Adapted from https://stackoverflow.com/a/68402011
'''

import asyncio
import logging
import re
import subprocess

from videof2b.core.common import is_linux, is_win

log = logging.getLogger(__name__)


if is_win():
    import winrt.windows.devices.enumeration as windows_devices

VIDEO_DEVICES = 4
PAT_VIDEO_SRC = re.compile(r'video(\d+)')


class CameraDevice:

    def __init__(self):
        self.cameras = []

    def get_camera_info(self) -> list:
        self.cameras = []
        self.cameras = self.add_camera_information()
        return self.cameras

    def add_camera_information(self) -> list:
        cameras = []

        if is_win():
            cameras_info_windows = asyncio.run(self.get_camera_information_for_windows())
            for camera_index, device in enumerate(cameras_info_windows):
                camera_name = device.name.replace('\n', '')
                cameras.append({'camera_index': camera_index, 'camera_name': camera_name})

        elif is_linux():
            # Dynamically discover the list of available "video\d+" devices and enumerate them.
            vstr = subprocess.run(
                ['ls', '/sys/class/video4linux'],
                stdout=subprocess.PIPE
            ).stdout.decode('utf8')
            log.debug(f'{vstr = }')
            video_sources = []
            if vstr:
                video_sources = [s for s in vstr.split('\n') if s]
                video_ids = [int(PAT_VIDEO_SRC.search(s).group(1)) for s in video_sources]
                video_sources = zip(video_ids, video_sources)
            log.debug(f'{video_sources = }')

            for camera_index, video_source in video_sources:
                camera_name = subprocess.run(
                    ['cat', f'/sys/class/video4linux/{video_source}/name'],
                    stdout=subprocess.PIPE
                ).stdout.decode('utf-8')
                camera_name = camera_name.replace('\n', '')
                if camera_name:
                    cameras.append({'camera_index': camera_index, 'camera_name': camera_name})

        return cameras

    async def get_camera_information_for_windows(self):
        return await windows_devices.DeviceInformation.find_all_async(VIDEO_DEVICES)
