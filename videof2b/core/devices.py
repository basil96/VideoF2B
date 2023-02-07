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
import platform
import subprocess

# import cv2

if platform.system() == 'Windows':
    import winrt.windows.devices.enumeration as windows_devices

VIDEO_DEVICES = 4


class CameraDevice:

    def __init__(self):
        self.cameras = []

    def get_camera_info(self) -> list:
        self.cameras = []

        # camera_indexes = self.get_camera_indexes()

        # if len(camera_indexes) == 0:
        # return self.cameras

        # self.cameras = self.add_camera_information(camera_indexes)
        self.cameras = self.add_camera_information()

        return self.cameras

    # TODO: confirmed on Win10 that it's not necessary to actually attempt starting a camera to find it. Confirm the same on Linux and hopefully Win7.
    # def get_camera_indexes(self):
    #     index = 0
    #     camera_indexes = []
    #     max_numbers_of_cameras_to_check = 10
    #     while max_numbers_of_cameras_to_check > 0:
    #         capture = cv2.VideoCapture(index)
    #         if capture.read()[0]:
    #             camera_indexes.append(index)
    #             capture.release()
    #         index += 1
    #         max_numbers_of_cameras_to_check -= 1
    #     return camera_indexes

    # def add_camera_information(self, camera_indexes: list) -> list:
    def add_camera_information(self) -> list:
        platform_name = platform.system()
        cameras = []

        if platform_name == 'Windows':
            cameras_info_windows = asyncio.run(self.get_camera_information_for_windows())
            for camera_index, device in enumerate(cameras_info_windows):
                camera_name = device.name.replace('\n', '')
                cameras.append({'camera_index': camera_index, 'camera_name': camera_name})

        elif platform_name == 'Linux':
            # TODO: why not just dynamically discover the list of available "video\d+" devices, and enumerate them?
            # for camera_index in camera_indexes:
            for camera_index in range(10):
                camera_name = subprocess.run(
                    ['cat', f'/sys/class/video4linux/video{camera_index}/name'],
                    stdout=subprocess.PIPE
                ).stdout.decode('utf-8')
                camera_name = camera_name.replace('\n', '')
                cameras.append({'camera_index': camera_index, 'camera_name': camera_name})

        return cameras

    async def get_camera_information_for_windows(self):
        return await windows_devices.DeviceInformation.find_all_async(VIDEO_DEVICES)
