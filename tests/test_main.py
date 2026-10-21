import importlib.util
import unittest
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_SPEC = importlib.util.spec_from_file_location(
    "image_processing", PROJECT_ROOT / "scripts" / "main.py"
)
image_processing = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(image_processing)


class ImageProcessingTests(unittest.TestCase):
    def test_minmax_stretch_maps_range_and_handles_constant_images(self):
        image = np.array([[20, 40], [60, 80]], dtype=np.uint8)

        stretched = image_processing.minmax_stretch(image)

        np.testing.assert_array_equal(
            stretched, np.array([[0, 85], [170, 255]], dtype=np.uint8)
        )
        np.testing.assert_array_equal(
            image_processing.minmax_stretch(np.full((2, 2), 42, dtype=np.uint8)),
            np.zeros((2, 2), dtype=np.uint8),
        )

    def test_analysis_returns_all_variant_outputs_as_uint8(self):
        image = np.zeros((64, 64), dtype=np.uint8)
        image[16:48, 20:44] = 180

        results = image_processing.analyze_image(image)

        self.assertEqual(
            set(results),
            {
                "Original",
                "Min-max contrast",
                "Histogram equalization",
                "Point detection (Laplacian)",
                "Line detection (Hough)",
                "Sobel edges",
                "Canny edges",
                "Sobel gradient magnitude",
            },
        )
        self.assertEqual(results["Line detection (Hough)"].shape, (64, 64, 3))
        for name, result in results.items():
            self.assertEqual(result.dtype, np.uint8, name)
            self.assertEqual(result.shape[:2], image.shape, name)

    def test_test_images_include_required_reproducible_variants(self):
        image = np.arange(64 * 64, dtype=np.uint8).reshape(64, 64)

        samples = image_processing.make_test_images(image)
        repeated_samples = image_processing.make_test_images(image)

        self.assertEqual(
            set(samples),
            {"Original sample", "Low contrast", "Noisy", "Blurred"},
        )
        for name, sample in samples.items():
            self.assertEqual(sample.shape, image.shape, name)
            np.testing.assert_array_equal(sample, repeated_samples[name])


if __name__ == "__main__":
    unittest.main()
