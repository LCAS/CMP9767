"""Keep the simulated RGBD consumer aligned with Fortress camera output."""

from pathlib import Path
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "cmp9767_tutorial" / "detector_3d.py"


class TestDetector3DSimulationContract(unittest.TestCase):
    def test_simulated_rgbd_uses_one_aligned_camera_info_topic(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn(
            "dcamera_info_topic = '/limo/depth_camera_link/depth/camera_info'", source
        )
        self.assertIn("self.dcamera_model = self.ccamera_model", source)
        self.assertIn("self.color2depth_aspect = 1.0", source)

    def test_color_processing_waits_for_calibration_and_synchronized_depth(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("ApproximateTimeSynchronizer", source)
        self.assertIn("self.image_sync.registerCallback(self.image_callback)", source)
        self.assertIn("if self.color2depth_aspect is None:", source)


if __name__ == "__main__":
    unittest.main()
