import unittest

from mente_do_brasil.constants import INVALID_SPATIAL_VALUES, LOCKED_SPATIAL_RESULTS


class LockedResultTests(unittest.TestCase):
    def test_locked_spatial_results_are_recorded(self):
        self.assertEqual(LOCKED_SPATIAL_RESULTS["global_moran_i"], 0.525494388844)
        self.assertEqual(LOCKED_SPATIAL_RESULTS["pseudo_p"], 0.0001)
        self.assertEqual(LOCKED_SPATIAL_RESULTS["permutations"], 9999)
        self.assertEqual(LOCKED_SPATIAL_RESULTS["seed"], 20260823)
        self.assertEqual(LOCKED_SPATIAL_RESULTS["lisa_fdr_significant"], 135)
        self.assertEqual(LOCKED_SPATIAL_RESULTS["hh"], 60)
        self.assertEqual(LOCKED_SPATIAL_RESULTS["ll"], 66)
        self.assertEqual(LOCKED_SPATIAL_RESULTS["hl"], 4)
        self.assertEqual(LOCKED_SPATIAL_RESULTS["lh"], 5)

    def test_invalid_old_moran_is_not_the_locked_result(self):
        self.assertNotEqual(
            LOCKED_SPATIAL_RESULTS["global_moran_i"],
            INVALID_SPATIAL_VALUES["old_global_moran_i"],
        )


if __name__ == "__main__":
    unittest.main()
