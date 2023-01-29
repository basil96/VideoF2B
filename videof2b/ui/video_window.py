# -*- coding: utf-8 -*-
# VideoF2B - Draw F2B figures from video
# Copyright (C) 2021  Andrey Vasilik - basil96
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
The video window of VideoF2B application.
'''
import logging
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from videof2b.core.common import get_bundle_dir
from videof2b.core.common.store import StoreProperties

log = logging.getLogger(__name__)


class VideoWindow(QtWidgets.QLabel):
    '''The window that displays video frames during processing.'''

    # Our signals
    point_added = QtCore.Signal(tuple)
    point_removed = QtCore.Signal(tuple)

    def __init__(self, parent: QtWidgets.QWidget, **kwargs) -> None:
        '''
        Create a new empty video window.

        kwargs:
            `enable_mouse` : Whether to enable mouse reactions.
                Also available via the `MouseEnabled` property.
                Default is False.
        '''
        super().__init__(parent, **kwargs)
        # The current image, original size
        self._pixmap = QtGui.QPixmap()
        # The currently displayed image in the UI
        self._scaled_pix_map = None
        # Internal flag for the is_mouse_enabled property
        self._is_mouse_enabled = kwargs.pop('enable_mouse', False)

    def update_frame(self, frame) -> None:
        '''Set a new video frame in the window.'''
        # log.debug('Entering VideoWindow.update_frame()')
        # log.debug(f'  source={repr(frame)}')
        self._pixmap = QtGui.QPixmap(QtGui.QPixmap.fromImage(frame))
        # log.debug(f'  self._pixmap = {self._pixmap}')
        self._update_pixmap(self.size())
        # log.debug('Leaving  VideoWindow.update_frame()')

    @property
    def is_mouse_enabled(self):
        '''Indicates whether the video window reacts to mouse events.'''
        return self._is_mouse_enabled

    @is_mouse_enabled.setter
    def is_mouse_enabled(self, val: bool) -> None:
        '''Setter for `is_mouse_enabled`'''
        self._is_mouse_enabled = val

    def _update_pixmap(self, size: QtCore.QSize) -> None:
        '''Rescale our pixmap to the given size.
        Always create the scaled pixmap from the original provided pixmap.'''
        if self._pixmap.isNull():
            # A null QPixmap has zero width, zero height and no contents.
            # You cannot draw in a null pixmap.
            return
        self._scaled_pix_map = self._pixmap.scaled(
            size,
            aspectMode=QtCore.Qt.KeepAspectRatio,
            mode=QtCore.Qt.SmoothTransformation)
        # TODO: center horizontally
        self.setPixmap(self._scaled_pix_map)

    def clear(self) -> None:
        '''Overridden method to clear our custom pixmap.'''
        self._pixmap = QtGui.QPixmap()
        return super().clear()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:  # pylint:disable=invalid-name
        '''Overridden event so that our window resizes with its parent
        while maintaining the loaded image's original aspect ratio.'''
        self._update_pixmap(event.size())
        self.update()
        event.accept()
        # return super().resizeEvent(event) # possible stack overflow?

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:  # pylint:disable=invalid-name
        '''Overridden event so that we react to mouse clicks as needed.'''
        if not self._is_mouse_enabled:
            return None
        options = {
            QtCore.Qt.LeftButton: self.point_added,
            QtCore.Qt.RightButton: self.point_removed
        }
        button = event.button()
        signal = options.get(button)
        return self._point_reaction(event.pos(), signal)

    def _get_image_point(self, pos: QtCore.QPoint) -> QtCore.QPoint:
        '''Determine the image coordinate of a clicked point
        with respect to the originally loaded image. If the determined
        coordinate is outside the original image bounds, return None.'''
        scaled_w, scaled_h = self._scaled_pix_map.size().toTuple()
        orig_w, orig_h = self._pixmap.size().toTuple()
        w_ratio = orig_w / scaled_w
        h_ratio = orig_h / scaled_h
        displayed_pixmap = self.pixmap()
        local_offset_y = 0.5 * (self.height() - displayed_pixmap.height())
        img_x = round(w_ratio * pos.x())
        img_y = round(h_ratio * (pos.y() - local_offset_y))
        if (img_x < 0 or img_x >= self._pixmap.width() or
                img_y < 0 or img_y >= self._pixmap.height()):
            return None
        return QtCore.QPoint(img_x, img_y)

    def _point_reaction(self, pos: QtCore.QPoint, signal: QtCore.Signal) -> None:
        '''React to a clicked point by emitting the specified signal.'''
        if signal is None:
            return
        img_point = self._get_image_point(pos)
        if img_point is not None:
            signal.emit(img_point.toTuple())


class LiveVideoWindow(QtWidgets.QWidget, StoreProperties):
    '''Live video window.

    Create this window when processing live video. Connect `VideoProcessor`'s
    `new_frame_available` signal to this window's `live_video_window` attribute's
    `update_frame` method to sync the video display in here with that in the
    main window.
    This window can be moved around and resized by the user.
    Full-screen state can be toggled by pressing `F` on the keyboard.
    '''

    def __init__(self, parent=None) -> None:
        super().__init__(parent, QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowTitleHint)
        self.setWindowTitle('Live Video')
        self.main_layout = QtWidgets.QVBoxLayout()
        self.live_video_window = VideoWindow(self)
        self.live_video_window.setMinimumSize(640, 360)
        self.main_layout.addWidget(self.live_video_window, stretch=1)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)
        action = QtGui.QAction(self)
        action.setText('Toggle fullscreen live video')
        action.setShortcut(QtCore.Qt.Key_F)
        self.act_fullscreen = action
        self.addAction(self.act_fullscreen)
        self.load_settings()
        # pylint: disable=no-member
        self.act_fullscreen.triggered.connect(self.on_toggle_fullscreen)

    def on_toggle_fullscreen(self):
        '''Toggle the window's full-screen state.
        '''
        if self.isFullScreen():
            self.set_fullscreen(False)
        else:
            self.set_fullscreen(True)

    def set_fullscreen(self, fullscreen: bool):
        '''Set the window's full-screen state.
        '''
        if fullscreen:
            self.setWindowState(QtCore.Qt.WindowFullScreen)
        else:
            self.setWindowState(QtCore.Qt.WindowNoState)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        '''Save this window's state before closing.
        '''
        self.save_settings()
        return super().closeEvent(event)

    def clear(self):
        '''Clear the live video window.

        Change the display to an image from disk if it exists.
        The searched image path is `../VideoF2B_live_videos/live_background.png`
        '''
        self.live_video_window.clear()
        bundle_path = get_bundle_dir()
        bg_img_path = bundle_path / '..' / 'VideoF2B_live_videos' / 'live_background.png'
        if bg_img_path.exists():
            img = QtGui.QImage(bg_img_path)
            self.live_video_window.update_frame(img)

    def load_settings(self):
        '''Load the settings of LiveVideoWindow.'''
        # TODO: This is very naive. Needs better knowledge of available screens so that this window always shows up on an existing screen.
        self.move(self.settings.value('ui/live_video_window_position'))
        self.restoreGeometry(self.settings.value('ui/live_video_window_geometry'))
        self.set_fullscreen(self.settings.value('ui/live_video_window_is_fullscreen'))

    def save_settings(self):
        '''Save the settings of LiveVideoWindow.'''
        self.settings.setValue('ui/live_video_window_position', self.pos())
        self.settings.setValue('ui/live_video_window_geometry', self.saveGeometry())
        self.settings.setValue('ui/live_video_window_is_fullscreen', self.isFullScreen())
