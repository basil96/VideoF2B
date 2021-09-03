import logging
from pathlib import Path

from videof2b.core.flight import Flight

log = logging.getLogger(__name__)


class TestSerialization:
    def test_flight_serialization(self):
        '''Test roundtrip serialization: writing and reading a Flight.'''
        test_path = Path(__file__).parent
        v = Path('..', 'TestVideos', 'new_ui', '1-four_leaf_clover.mp4')
        assert v.exists()
        c = Path('..', 'cal', 'SONY-A57 10-20@10mm', 'as normal', 'CamCalibration.npz')
        assert c.exists()
        pts = [
            (942., 1001.),
            (936.,  962.),
            (519.,  964.),
            (1348.,  954.)
        ]
        R = 21.336
        mr = 25.
        mh = 1.51
        so = (1., -0.7, 0.)
        f1 = Flight(
            v,
            False,
            c,
            flight_radius=R,
            marker_radius=mr,
            marker_height=mh,
            sphere_offset=so,
            loc_pts=pts
        )
        flight_path = test_path.with_suffix('.flight')
        f1.write(flight_path)
        assert flight_path.exists()
        f2 = Flight.read(flight_path)
        assert f1.video_path == f2.video_path == v
        assert f1.calibration_path == f2.calibration_path == c
        assert f1.is_calibrated == f2.is_calibrated == True
        assert f1.is_located == f2.is_located == True
        assert f1.is_live == f2.is_live == False
        assert f1.flight_radius == f2.flight_radius == R
        assert f1.marker_radius == f2.marker_radius == mr
        assert f1.marker_height == f2.marker_height == mh
        assert f1.sphere_offset == f2.sphere_offset == so
        assert f1.loc_pts == f2.loc_pts == pts
