import unittest

from mente_do_brasil.constants import EXPECTED_HEALTH_REGION_COUNT
from mente_do_brasil.quality import MissingKind, percentile_rank, validate_health_region_table


def make_valid_region_rows():
    rows = []
    for index in range(EXPECTED_HEALTH_REGION_COUNT):
        rows.append(
            {
                "health_region_code": f"HR{index + 1:03d}",
                "population": 100000 + index,
                "caps_count": index % 5,
                "mental_health_beds_sus": index % 7,
                "psychiatrist_fte": float(index % 11),
                "suicide_asmr_percentile": 0.5,
                "psychiatric_admission_rate_percentile": 0.5,
                "caps_rate_percentile": 0.5,
                "mental_health_beds_sus_rate_percentile": 0.5,
                "psychiatrist_fte_rate_percentile": 0.5,
                "need_score": 0.5,
                "capacity_score": 0.5,
                "mismatch_score": 0.0,
            }
        )
    return rows


class MetricContractTests(unittest.TestCase):
    def test_valid_region_table_passes(self):
        issues = validate_health_region_table(make_valid_region_rows())
        self.assertEqual(issues, [])

    def test_negative_counts_are_rejected(self):
        rows = make_valid_region_rows()
        rows[0]["psychiatrist_fte"] = -1

        issues = validate_health_region_table(rows)

        self.assertTrue(any(issue.rule == "psychiatrist_fte_nonnegative" for issue in issues))

    def test_scores_are_bounded(self):
        rows = make_valid_region_rows()
        rows[0]["need_score"] = 1.2
        rows[1]["mismatch_score"] = -1.2

        issues = validate_health_region_table(rows)

        self.assertTrue(any(issue.rule == "need_score_bounded" for issue in issues))
        self.assertTrue(any(issue.rule == "mismatch_score_bounded" for issue in issues))

    def test_percentile_rank_preserves_missing_and_zero(self):
        ranks = percentile_rank([0, 10, None, MissingKind.NOT_AVAILABLE.value])

        self.assertEqual(ranks[0], 0.0)
        self.assertEqual(ranks[1], 1.0)
        self.assertIsNone(ranks[2])
        self.assertEqual(ranks[3], MissingKind.NOT_AVAILABLE.value)


if __name__ == "__main__":
    unittest.main()
