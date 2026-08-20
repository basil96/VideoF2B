# VideoF2B

[![Documentation Status](https://readthedocs.org/projects/videof2b/badge/?version=latest)](https://videof2b.readthedocs.io/en/latest/?badge=latest)

Author's blog is [here](http://videof2b.blogspot.com/)

VideoF2B is an open-source desktop application for tracing F2B Control Line Stunt competition flight figures in video.

## Overview

Use this application to trace the path of a control line aircraft as it performs aerobatic maneuvers in F2B competition
and compare it to regulation figures.

Authors: Alberto Solera, Andrey Vasilik

## Documentation

Online documentation is [here](http://videof2b.readthedocs.io/).

## Features

- Detects the movement of the aircraft and draw the trace of its centroid in video.

- Draws an augmented-reality (AR) hemisphere that represents the flight envelope.

- Displays template figures on the surface of the AR sphere according to
Paragraph F2B.13 - "Description of Manoeuvres" of the
[FAI Sporting Code (Edition 2026)](https://www.fai.org/sites/default/files/document/file/SC4_volume_F2_ControlLine_2026_1.pdf).
Manoeuvre diagrams are available in
[Annex 4J (Edition 2026)](https://www.fai.org/sites/default/files/2026-05/sc4_vol_f2_controlline_annex_4j_26.pdf)
The latest versions of these regulations are available at the
[FAI Sporting Code page](https://www.fai.org/page/sporting-code) under **Section 4 (Aeromodelling)**.

- Allows the user to rotate and translate the AR sphere during video processing.

- Includes a utility to perform camera calibration. This enables display of the AR sphere in videos.

- Includes a utility to estimate the best camera placement in the field.

## Features (planned)

- Process live video in real time.

- Project the detected points into the virtual sphere in engineering units to track the aircraft in 3D.

- Perform the best possible fit of executed figures to the nominal figures.

- Determine a score per figure.

## Developer installation

### All platforms

- Create a virtual environment.

- Clone the project from this repository and `cd` into the root directory.

- Run `pip install -e .` in the virtual environment. This installs the required packages for development work, testing, and building of releases.

### Linux

- Build OpenCV **5.0.0** (matches the Windows `opencv-python==5.0.0.93` pin) for the virtual environment based on the instructions [here](https://www.pyimagesearch.com/2018/08/15/how-to-install-opencv-4-on-ubuntu/) — the guide predates OpenCV 5, but the same steps apply; just clone the `5.0.0` tag — with these changes:
  - Add `-D WITH_QT=OFF -D WITH_GTK=ON` to the `cmake` command (and install `libgtk-3-dev`). OpenCV's own bundled Qt plugins otherwise conflict with PySide6's at runtime.
  - On newer Ubuntu releases (26.04+), `libatlas-base-dev` is no longer packaged; use `libopenblas-dev liblapack-dev` instead.
  - Point `-D PYTHON3_EXECUTABLE` and `-D PYTHON3_PACKAGES_PATH` at your virtual environment's `python` and `site-packages` so the built `cv2` module installs directly into it.
- **Do not substitute the `opencv-python` pip wheel on Linux**, even though it's tempting to skip the build. Its bundled static FFmpeg registers the `h264_v4l2m2m` hardware encoder (meant for ARM SBCs like Raspberry Pi) ahead of software `libx264`, so `cv2.VideoWriter` with the app's `H264` fourcc fails outright on any machine without that hardware (`VIDEOIO/FFMPEG: Failed to initialize VideoWriter`) — video export is broken, even though calibration and playback look fine. Building from source links the system's real FFmpeg and doesn't hit this.

## Building a release

- **IMPORTANT:** Create a clean virtual environment.  Do not update `setuptools` in it. Verify that
  `setuptools` version is `56.0.0` via `pip show setuptools`. (This applies to the legacy Python 3.8/3.9 toolchain; a modernized stack on Python 3.14 has been verified to build correctly with setuptools 84.0.0 instead.)

- Install `python3-tk` and `libxcb-cursor0` (Linux) before building. PyInstaller's splash screen requires `tkinter` to be importable in the build environment's Python, and the frozen app needs `libxcb-cursor.so.0` at runtime for Qt's `xcb` platform plugin. Without these, `build_exe` fails or the resulting binary won't run on a machine that lacks them.

- Tag the latest stable commit in `master` with the desired version using a scheme that complies with PEP 440.

- Switch to the project's root directory.

- Enter (activate) the project's virtual environment. This must be a real shell activation
  (e.g. `source .venv/bin/activate`), not just invoking `.venv/bin/python` directly — `build_exe`
  shells out to the `pyinstaller` command by name, which is only found if the venv's `bin`
  directory is on `PATH`.

- Run the following commands:

```shell
    pip install -e .
    python setup.py build_exe
```

- The first command installs the latest version of the project locally and updates
the version file `videof2b/version.py` according to the state of the project's current Git tree.
The second command invokes PyInstaller and builds a binary end-user executable in the `dist` directory.

- Test the executable on target platforms.

- Publish the release to the world.

## Building documentation

- Switch to the project's root directory.

- Enter the project's virtual environment.

- Run `pip install -e .[docs]`. This installs the latest version of the project and the `docs` extras locally.

- Switch to the `docs` directory.

- Run `make html` or `make latex` (`make.bat ...` on Windows) according to your target needs.
The typical target is `html`. The resulting pages will be in the `docs/build` directory.

- After making changes to documentation as needed, run `make <target>` to verify the results locally.
If necessary during development, run `make clean` to wipe the generated documentation files.

- This project's documentation is hosted on [Read the Docs](https://readthedocs.org/).
When ready to publish, just push the changes to the main remote Git repository.
Every push to the main repository triggers a new build of documentation on RTD.
The build typically takes just a few minutes.
Verify that the documentation build passes (see the "docs" badge at the top of this README).
Verify that the online documentation reflects your changes.

## External Dependencies

See **setup.cfg**.

**IMPORTANT:** at this time the `imutils` package used for development is a modified fork of the official package.
