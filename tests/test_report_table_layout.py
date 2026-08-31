import pytest
from reportlab.lib.units import cm

from api.services.manager import simple_table


@pytest.mark.parametrize("columns", [2, 3])
def test_report_table_columns_fit_printable_width(columns):
    table = simple_table([["Header"] * columns, ["Value"] * columns])
    width, height = table.wrap(17 * cm, 25 * cm)
    assert width == pytest.approx(16.2 * cm)
    assert len(table._colWidths) == columns
    assert height > 0
