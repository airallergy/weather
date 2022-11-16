from pathlib import Path

import pytest
import pandas as pd

from weather import EPW

WEATHER_TESTS_DIRECTORY = Path(__file__).parent
WEATHER_TESTS_DATA = WEATHER_TESTS_DIRECTORY / "data"


@pytest.fixture(scope="session")
def epw():
    return EPW.from_epw(WEATHER_TESTS_DATA / "test_epw.epw")


@pytest.fixture
def header(request, epw):
    return getattr(epw, request.param)


@pytest.mark.parametrize(
    "header, expected_results",
    tuple(
        {
            "location": (
                "LONDON/GATWICK",
                "-",
                "GBR",
                "IWEC Data",
                "037760",
                51.15,
                -0.18,
                0.0,
                62.0,
            ),
            "design_conditions": (1, "Climate Design Data 2009 ASHRAE Handbook", ""),
            "typical_extreme_periods": (6,),
            "ground_temperatures": (3,),
            "holidays_daylight_saving": ("No", "0", "0", 0),
            "comments_1": (
                '''"IWEC- WMO#037760 - Europe -- Original Source Data (c) 2001 American Society of Heating, Refrigerating and Air-Conditioning Engineers (ASHRAE), Inc., Atlanta, GA, USA.  www.ashrae.org  All rights reserved as noted in the License Agreement and Additional Conditions. DISCLAIMER OF WARRANTIES: The data is provided 'as is' without warranty of any kind, either expressed or implied. The entire risk as to the quality and performance of the data is with you. In no event will ASHRAE or its contractors be liable to you for any damages, including without limitation any lost profits, lost savings, or other incidental or consequential damages arising out of the use or inability to use this data."''',
            ),
            "comments_2": (
                " -- Ground temps produced with a standard soil diffusivity of 2.3225760E-03 {m**2/day}",
            ),
            "data_periods": (1, 1),
        }.items()
    ),
    indirect=("header",),
)
def test_metafields(header, expected_results):
    for idx, (metafield_name, metafield_type) in enumerate(header.metafields.items()):
        expected_result = expected_results[idx]
        if metafield_type is float:
            assert getattr(header, metafield_name) == pytest.approx(expected_result)
        else:
            assert getattr(header, metafield_name) == expected_result


@pytest.mark.parametrize(
    "header, expected_results",
    tuple(
        {
            "location": None,
            # "design_conditions": False,
            "typical_extreme_periods": (
                (
                    "Summer - Week Nearest Max Temperature For Period",
                    "Extreme",
                    "8/17",
                    "8/23",
                ),
                (
                    "Summer - Week Nearest Average Temperature For Period",
                    "Typical",
                    "6/29",
                    "7/ 5",
                ),
                (
                    "Winter - Week Nearest Min Temperature For Period",
                    "Extreme",
                    "12/ 1",
                    "12/ 7",
                ),
                (
                    "Winter - Week Nearest Average Temperature For Period",
                    "Typical",
                    "1/20",
                    "1/26",
                ),
                (
                    "Autumn - Week Nearest Average Temperature For Period",
                    "Typical",
                    "11/10",
                    "11/16",
                ),
                (
                    "Spring - Week Nearest Average Temperature For Period",
                    "Typical",
                    "4/19",
                    "4/25",
                ),
            ),
            "ground_temperatures": (
                (
                    0.5,
                    float("nan"),
                    float("nan"),
                    float("nan"),
                    4.16,
                    5.30,
                    7.51,
                    9.61,
                    13.58,
                    15.67,
                    16.24,
                    15.18,
                    12.74,
                    9.69,
                    6.69,
                    4.70,
                ),
                (
                    2,
                    float("nan"),
                    float("nan"),
                    float("nan"),
                    5.73,
                    6.01,
                    7.27,
                    8.68,
                    11.72,
                    13.67,
                    14.64,
                    14.43,
                    13.03,
                    10.93,
                    8.56,
                    6.69,
                ),
                (
                    4,
                    float("nan"),
                    float("nan"),
                    float("nan"),
                    7.35,
                    7.16,
                    7.71,
                    8.51,
                    10.52,
                    12.03,
                    13.01,
                    13.25,
                    12.64,
                    11.40,
                    9.79,
                    8.34,
                ),
            ),
            "holidays_daylight_saving": (),
            "comments_1": None,
            "comments_2": None,
            "data_periods": (("Data", "Sunday", " 1/ 1", "12/31"),),
        }.items()
    ),
    indirect=("header",),
)
def test_header_fields(header, expected_results):
    if expected_results is None:
        assert "fields" not in header.__class__.__dict__
    else:
        expected_vars = tuple(zip(*expected_results))
        for idx, (field_name, field_type) in enumerate(header.fields.items()):
            expected_var = expected_vars[idx] if expected_results else ()
            if field_type is float:
                assert getattr(header, field_name) == pytest.approx(
                    expected_var, nan_ok=True
                )
            else:
                assert getattr(header, field_name) == expected_var


def test_data_fields(epw):
    expected_results = tuple(
        pd.read_csv(
            WEATHER_TESTS_DATA / "test_epw.epw",
            skiprows=8,
            names=epw.fields.keys(),
            dtype=epw.fields,
        ).itertuples(index=False, name=None)
    )
    expected_vars = tuple(zip(*expected_results))
    for idx, (field_name, field_type) in enumerate(epw.fields.items()):
        expected_var = expected_vars[idx]
        if field_type is float:
            assert getattr(epw, field_name) == pytest.approx(expected_var)
        else:
            assert getattr(epw, field_name) == expected_var
