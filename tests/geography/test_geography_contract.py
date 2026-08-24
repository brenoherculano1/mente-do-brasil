import unittest

from mente_do_brasil.constants import EXPECTED_HEALTH_REGION_COUNT, EXPECTED_MUNICIPALITY_COUNT
from mente_do_brasil.quality import detect_silent_join_loss, validate_geography_crosswalk


def make_valid_crosswalk():
    rows = []
    for municipality_index in range(EXPECTED_MUNICIPALITY_COUNT):
        region_index = municipality_index % EXPECTED_HEALTH_REGION_COUNT
        rows.append(
            {
                "municipality_code": f"{municipality_index + 1:07d}",
                "health_region_code": f"HR{region_index + 1:03d}",
                "uf": "SP",
            }
        )
    return rows


class GeographyContractTests(unittest.TestCase):
    def test_valid_crosswalk_has_5570_municipalities_and_439_regions(self):
        issues = validate_geography_crosswalk(make_valid_crosswalk())
        self.assertEqual(issues, [])

    def test_duplicate_municipality_is_rejected(self):
        rows = make_valid_crosswalk()
        rows[-1]["municipality_code"] = rows[0]["municipality_code"]

        issues = validate_geography_crosswalk(rows)

        self.assertTrue(any(issue.rule == "municipality_count" for issue in issues))
        self.assertTrue(any(issue.rule == "one_region_per_municipality" for issue in issues))

    def test_invalid_uf_is_rejected(self):
        rows = make_valid_crosswalk()
        rows[0]["uf"] = "XX"

        issues = validate_geography_crosswalk(rows)

        self.assertTrue(any(issue.rule == "valid_uf" for issue in issues))

    def test_join_loss_is_detected(self):
        issues = detect_silent_join_loss(["001", "002", "003"], ["001", "003"], key_name="municipality_code")

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule, "no_silent_join_loss")


if __name__ == "__main__":
    unittest.main()
