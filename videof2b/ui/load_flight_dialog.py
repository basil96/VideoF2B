# -*- coding: utf-8 -*-
# VideoF2B - Draw F2B figures from video
# Copyright (C) 2021 - 2023  Andrey Vasilik - basil96
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
The dialog that loads the input video.
'''

import logging
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from videof2b.core.common import (DEFAULT_FLIGHT_RADIUS, DEFAULT_MARKER_HEIGHT,
                                  DEFAULT_MARKER_RADIUS)
from videof2b.core.common.path import path_to_str, str_to_path
from videof2b.core.common.store import StoreProperties
from videof2b.core.devices import CameraDevice
from videof2b.core.flight import Flight
from videof2b.ui import EXTENSIONS_VIDEO
from videof2b.ui.widgets import PathEdit, PathEditType

log = logging.getLogger(__name__)


class LoadFlightDialog(QtWidgets.QDialog, StoreProperties):
    '''The dialog window that collects user inputs for a Flight instance.'''

    # All the video frame rates that exist today
    _video_input_rates = (
        23.98,
        24.,
        25.,
        29.97,
        30.,
        50.,
        59.94,
        60.,
    )

    def __init__(self, parent) -> None:
        '''Constructor.'''
        super().__init__(
            parent,
            QtCore.Qt.WindowSystemMenuHint |
            QtCore.Qt.WindowTitleHint |
            QtCore.Qt.WindowCloseButtonHint
        )
        # TODO: try to implement this UI with a QAbstractListModel or a QStandardItemModel
        #       for proper cohesion.
        # see https://doc.qt.io/qtforpython/overviews/model-view-programming.html#models
        self.flight = None
        self.is_live_decimator_enabled = self.settings.value('core/enable_live_decimator')
        self.show_live_video_window = self.settings.value('ui/show_live_video_window')
        self.mru_cam_loc_pts = self.settings.value('mru/cam_loc_pts')
        log.debug(f'{self.mru_cam_loc_pts = }')
        self.setup_ui()
        self.setWindowTitle('Load a Flight')
        # pylint: disable=no-member
        self.on_live_state_changed()
        self.live_chk.stateChanged.connect(self.on_live_state_changed)
        self.live_decimate_chk.stateChanged.connect(self.on_live_decimate_state_changed)
        self.live_show_vidwin_chk.stateChanged.connect(self.on_live_show_vidwin_state_changed)
        self.skip_locate_chk.stateChanged.connect(self.on_skip_locate_changed)
        self.cancel_btn.clicked.connect(self.reject)
        self.load_btn.clicked.connect(self.accept)

    def setup_ui(self):
        '''Lay out the UI elements'''
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setObjectName('main_layout')
        self.video_path_lbl = QtWidgets.QLabel('Video source:', self)

        is_live_video_enabled = self.settings.value('core/enable_live_video')
        use_live_video = self.settings.value('mru/use_live_video')
        use_mru_cam_loc = self.settings.value('mru/use_cam_loc')
        self.live_chk = QtWidgets.QCheckBox('&Live video', self)
        self.live_device_list = QtWidgets.QComboBox(self)
        self.live_rates_lbl = QtWidgets.QLabel('Input frame rate:', self)
        self.live_rates_list = QtWidgets.QComboBox(self)
        self.live_rates_list.addItems([str(x) for x in self._video_input_rates])
        self.live_rates_list.setCurrentIndex(self.settings.value('mru/live_video_input_fps_idx'))
        self.live_rates_list.setToolTip('Match this value to your live video\'s input frame rate.')
        self.live_decimate_chk = QtWidgets.QCheckBox('Decimate input by 1/2', self)
        self.live_decimate_chk.setChecked(self.is_live_decimator_enabled)
        self.live_show_vidwin_chk = QtWidgets.QCheckBox('Show live video window', self)
        self.live_show_vidwin_chk.setChecked(self.show_live_video_window)
        self.live_name_lbl = QtWidgets.QLabel('Stream label:', self)
        self.live_name_txt = QtWidgets.QLineEdit('LiveStream', self)
        self.live_chk.setChecked(use_live_video)
        self.live_chk.setVisible(is_live_video_enabled)

        self.video_path_txt = PathEdit(
            self, PathEditType.FILES,
            'Select video file',
            self.settings.value('mru/video_dir')
        )
        self.video_path_txt.filters = f'Video files ({" ".join(EXTENSIONS_VIDEO)});;All files (*)'
        #
        # TODO: insert a checkbox here that connects to `flight.is_ar_enabled`
        #       and conditionally enables/disables the entire "calibrated" group of inputs below.
        #
        self.cal_path_lbl = QtWidgets.QLabel('Calibration file:', self)
        self.cal_path_txt = PathEdit(
            self, PathEditType.FILES,
            'Select calibration file',
            self.settings.value('mru/cal_dir')
        )
        self.cal_path_txt.filters = 'Calibration files (*.npz);;All files (*)'
        self.skip_locate_chk = QtWidgets.QCheckBox('&Skip camera location', self)
        self.use_mru_cam_location = QtWidgets.QCheckBox('Use last known &camera location', self)
        self.use_mru_cam_location.setChecked(use_mru_cam_loc)
        # Measurement inputs
        self.flight_radius_lbl = QtWidgets.QLabel(
            'Flight radius (m)', self)
        self.marker_radius_lbl = QtWidgets.QLabel(
            'Height markers: distance to center (m)', self)
        self.marker_height_lbl = QtWidgets.QLabel(
            'Height markers: height above center of circle (m)', self)
        flight_radius = DEFAULT_FLIGHT_RADIUS
        marker_radius = DEFAULT_MARKER_RADIUS
        marker_height = DEFAULT_MARKER_HEIGHT
        if use_live_video:
            # Use MRU values for faster live workflow
            flight_radius = self.settings.value('mru/flight_radius')
            marker_radius = self.settings.value('mru/marker_radius')
            marker_height = self.settings.value('mru/marker_height')
        self.flight_radius_txt = QtWidgets.QLineEdit(f'{flight_radius:.1f}', self)
        self.marker_radius_txt = QtWidgets.QLineEdit(f'{marker_radius:.1f}', self)
        self.marker_height_txt = QtWidgets.QLineEdit(f'{marker_height:.2f}', self)
        self.meas_grid = QtWidgets.QGridLayout()
        self.meas_grid.setObjectName('meas_grid')
        self.meas_grid.addWidget(self.flight_radius_lbl, 1, 1, 1, 1)
        self.meas_grid.addWidget(self.flight_radius_txt, 1, 2, 1, 1)
        self.meas_grid.addWidget(self.marker_radius_lbl, 2, 1, 1, 1)
        self.meas_grid.addWidget(self.marker_radius_txt, 2, 2, 1, 1)
        self.meas_grid.addWidget(self.marker_height_lbl, 3, 1, 1, 1)
        self.meas_grid.addWidget(self.marker_height_txt, 3, 2, 1, 1)
        #
        self.load_btn = QtWidgets.QPushButton('Load', self)
        self.load_btn.setDefault(True)
        self.cancel_btn = QtWidgets.QPushButton('Cancel', self)
        self.bottom_layout = QtWidgets.QHBoxLayout()
        self.bottom_layout.addWidget(self.load_btn)
        self.bottom_layout.addWidget(self.cancel_btn)
        self.main_layout.addWidget(self.live_chk)
        self.main_layout.addWidget(self.video_path_lbl)
        self.main_layout.addWidget(self.live_device_list)
        self.main_layout.addWidget(self.live_rates_lbl)
        self.main_layout.addWidget(self.live_rates_list)
        self.main_layout.addWidget(self.live_decimate_chk)
        self.main_layout.addWidget(self.live_show_vidwin_chk)
        self.main_layout.addWidget(self.live_name_lbl)
        self.main_layout.addWidget(self.live_name_txt)
        self.main_layout.addWidget(self.video_path_txt)
        self.main_layout.addWidget(self.cal_path_lbl)
        self.main_layout.addWidget(self.cal_path_txt)
        self.main_layout.addWidget(self.skip_locate_chk)
        self.main_layout.addWidget(self.use_mru_cam_location)
        self.main_layout.addLayout(self.meas_grid)
        self.main_layout.addSpacerItem(QtWidgets.QSpacerItem(20, 20))
        self.main_layout.addLayout(self.bottom_layout)

    def accept(self) -> None:
        '''Create a Flight instance if all inputs are valid.
        Store the instance as our `flight` attribute.
        '''
        if not self._validate():
            return None  # Keeps the window up
        is_live = self.live_chk.isChecked()
        video_path = self.video_path_txt.path
        cam_idx = None
        live_fps_value = None
        use_mru_cam_loc = self.use_mru_cam_location.isChecked()
        # TODO: use proper validation for these numeric fields!
        flight_radius = float(self.flight_radius_txt.text())
        marker_radius = float(self.marker_radius_txt.text())
        marker_height = float(self.marker_height_txt.text())
        if is_live:
            box_idx = self.live_device_list.currentIndex()
            cam_idx = self.live_device_list.itemData(box_idx)
            self.settings.setValue('mru/live_device_idx', cam_idx)
            self.settings.setValue('mru/live_device_name', self.live_device_list.itemText(box_idx))
            self.settings.setValue('mru/live_video_input_fps_idx', self.live_rates_list.currentIndex())
            video_path = Path(self.live_name_txt.text())
            live_fps_value = self._video_input_rates[self.live_rates_list.currentIndex()]
            self.settings.setValue('mru/flight_radius', flight_radius)
            self.settings.setValue('mru/marker_radius', marker_radius)
            self.settings.setValue('mru/marker_height', marker_height)
            self.settings.setValue('core/enable_live_decimator', self.is_live_decimator_enabled)
            self.settings.setValue('ui/show_live_video_window', self.show_live_video_window)
        self.settings.setValue('mru/use_live_video', is_live)
        loc_pts = []
        if use_mru_cam_loc:
            loc_pts = self.settings.value('mru/cam_loc_pts')
        self.flight = Flight(
            video_path,
            is_live=is_live,
            cal_path=self.cal_path_txt.path,
            cam_index=cam_idx,
            live_fps=live_fps_value,
            enable_decimator=self.is_live_decimator_enabled,
            skip_locate=self.skip_locate_chk.isChecked(),
            flight_radius=flight_radius,
            marker_radius=marker_radius,
            marker_height=marker_height,
            loc_pts=loc_pts,
            # TODO: include `sphere_offset` as well. Add a grid widget to UI for the XYZ values.
        )
        if not is_live:
            self.settings.setValue('mru/video_dir', self.video_path_txt.path.parent)
        # Cal path is optional, so check it first
        cal_path = self.cal_path_txt.path
        if path_to_str(cal_path) and cal_path.exists():
            self.settings.setValue('mru/cal_dir', cal_path.parent)
        self.settings.setValue('mru/use_cam_loc', self.use_mru_cam_location.isChecked())
        # Do not proceed if flight failed to load
        if not self.flight.is_ready:
            QtWidgets.QMessageBox.critical(
                self, 'Error',
                'Failed to load video source.',
                QtWidgets.QMessageBox.Ok
            )
            return None  # Keeps the window up
        return super().accept()

    def on_skip_locate_changed(self):
        '''Enable/disable the measurement widgets when the "skip locate" checkbox changes.'''
        enable = not self.sender().isChecked()
        self.flight_radius_lbl.setEnabled(enable)
        self.flight_radius_txt.setEnabled(enable)
        self.marker_radius_lbl.setEnabled(enable)
        self.marker_radius_txt.setEnabled(enable)
        self.marker_height_lbl.setEnabled(enable)
        self.marker_height_txt.setEnabled(enable)

    def _validate(self) -> bool:
        '''Validate user inputs.'''
        result = True
        # TODO: this is rudimentary for now. Using a Qt Model with field validators would be more ideal.
        # Then we could highlight invalid fields instead of popping up a bunch of error messageboxes.
        if not self.live_chk.isChecked():
            if not self._validate_path(self.video_path_txt.path, 'Please specify a valid video source.'):
                result = False
        else:
            if not self.live_name_txt.text().strip():
                self._show_error_message('Please enter a stream name.')
                result = False
        # TODO: calibration path can only be validated if we add a "is calibrated" checkbox
        #       to this dialog that enables AR-related data.
        # if not self._validate_path(self.cal_path_txt.path, 'Please specify a valid calibration file.'):
        #     result = False
        try:
            float(self.flight_radius_txt.text())
            float(self.marker_radius_txt.text())
            float(self.marker_height_txt.text())
        except ValueError as err:
            self._show_error_message(f'ERROR: {err}\nPlease verify numeric inputs.')
            result = False
        return result

    def _validate_path(self, path: Path, err_msg: str) -> bool:
        '''Validate a path input. Show an error message
        if path is empty or doesn't exist.'''
        if path is None or not path.exists():
            self._show_error_message(err_msg)
            return False
        return True

    def _show_error_message(self, msg):
        '''Display a simple error messagebox to user.'''
        QtWidgets.QMessageBox.critical(self, 'Error', msg, QtWidgets.QMessageBox.Ok)

    def on_live_state_changed(self):
        '''Update UI when the state of the "is live" checkbox changes.'''
        is_live = self.live_chk.isChecked()
        self.live_device_list.setVisible(is_live)
        self.live_rates_lbl.setVisible(is_live)
        self.live_rates_list.setVisible(is_live)
        self.live_decimate_chk.setVisible(is_live)
        self.live_show_vidwin_chk.setVisible(is_live)
        self.live_name_lbl.setVisible(is_live)
        self.live_name_txt.setVisible(is_live)
        self.video_path_txt.setVisible(not is_live)
        if is_live:
            self._populate_live_list()
            # Set the "use MRU cam location" checkbox whenever user switches to live video.
            self.use_mru_cam_location.setChecked(True)

    def on_live_decimate_state_changed(self):
        '''Update the decimator setting.'''
        self.is_live_decimator_enabled = self.sender().isChecked()

    def on_live_show_vidwin_state_changed(self):
        '''Update the live video window visibility setting.'''
        self.show_live_video_window = self.sender().isChecked()

    def _populate_live_list(self):
        '''Populate the list of live devices on demand.'''
        cam = CameraDevice()
        devices = cam.get_camera_info()
        mru_cam_idx = self.settings.value('mru/live_device_idx')
        mru_list_idx = None
        self.live_device_list.clear()
        for i, device in enumerate(devices):
            cam_idx = device['camera_index']
            cam_name = device['camera_name']
            self.live_device_list.addItem(cam_name, userData=cam_idx)
            if cam_idx == mru_cam_idx:
                mru_list_idx = i
        if mru_list_idx is not None:
            if self.live_device_list.itemText(mru_list_idx) == self.settings.value('mru/live_device_name'):
                self.live_device_list.setCurrentIndex(mru_list_idx)
