import unittest
import threading
import urllib.error
import urllib.request

import numpy as np

import server


class RegionMatchingTests(unittest.TestCase):
    def test_camera_polygon_matches_detection_center(self):
        config = {
            "coordinate_system": "normalized_camera_image",
            "slots": [
                {
                    "id": "B1-001",
                    "slot_index": 0,
                    "kind": "normal",
                    "polygon": [[0.1, 0.1], [0.4, 0.1], [0.4, 0.5], [0.1, 0.5]],
                }
            ],
        }
        detections = [
            {"bbox_normalized": [0.15, 0.2, 0.1, 0.1], "score": 0.9}
        ]

        results, ready, strategy = server.match_detections_to_regions(
            detections, config
        )

        self.assertTrue(ready)
        self.assertEqual(strategy, "camera_roi")
        self.assertEqual(results[0]["status"], "occupied")

    def test_homography_transforms_camera_point_before_matching(self):
        config = {
            "coordinate_system": "normalized_plan",
            "calibration": {
                "camera_points": [[0, 0], [1, 0], [1, 1], [0, 1]],
                "plan_points": [[0.1, 0.1], [0.9, 0.1], [0.9, 0.9], [0.1, 0.9]],
            },
            "slots": [
                {
                    "id": "B1-001",
                    "slot_index": 0,
                    "kind": "normal",
                    "polygon": [[0.42, 0.42], [0.58, 0.42], [0.58, 0.58], [0.42, 0.58]],
                }
            ],
        }
        detections = [
            {"bbox_normalized": [0.45, 0.45, 0.1, 0.1], "score": 0.9}
        ]

        results, ready, strategy = server.match_detections_to_regions(
            detections, config
        )

        self.assertTrue(ready)
        self.assertEqual(strategy, "homography")
        self.assertEqual(results[0]["status"], "occupied")
        self.assertTrue(np.allclose(detections[0]["match_point"], [0.5, 0.5]))

    def test_plan_coordinates_require_calibration(self):
        config = {"coordinate_system": "normalized_plan", "slots": [{}]}
        results, ready, strategy = server.match_detections_to_regions([], config)
        self.assertFalse(ready)
        self.assertEqual(results, [])
        self.assertEqual(strategy, "missing_homography_calibration")


class StabilityTests(unittest.TestCase):
    def test_occupied_slot_requires_two_empty_results_to_clear(self):
        worker = server.AnalysisWorker()
        occupied = {"id": "B1-001", "status": "occupied"}
        empty = {"id": "B1-001", "status": "empty"}

        self.assertEqual(worker._stabilize([occupied])[0]["status"], "occupied")
        self.assertEqual(worker._stabilize([empty])[0]["status"], "occupied")
        self.assertEqual(worker._stabilize([empty])[0]["status"], "empty")


class EdgeApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = server.ThreadingHTTPServer(
            ("127.0.0.1", 0), server.ParkViewHandler
        )
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.httpd.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=2)

    def test_health_allows_web_app_origin(self):
        with urllib.request.urlopen(f"{self.base_url}/api/health") as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(
                response.headers["Access-Control-Allow-Origin"],
                server.ALLOWED_ORIGIN,
            )

    def test_environment_file_is_not_public(self):
        with self.assertRaises(urllib.error.HTTPError) as context:
            urllib.request.urlopen(f"{self.base_url}/.env")
        self.assertEqual(context.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
