from ._tools import AnyFieldSchema

_EPW_SCHEMA: dict[str, dict[str, AnyFieldSchema]] = {
    "location": {
        "metafields": {
            "city": str,
            "state_province_region": str,
            "country": str,
            "source": str,
            "wmo": str,
            "latitude": float,
            "longitude": float,
            "timezone": float,
            "elevation": float,
        }
    },
    "design_conditions": {
        "metafields": {
            "number_of_design_conditions": int,
            "design_condition_source": str,
            "unknwon_field": str,
        },
        "fields": {"design_conditions": str},
    },
    "typical_extreme_periods": {
        "metafields": {"number_of_typical_extreme_periods": int},
        "fields": {
            "period_name": str,
            "period_type": str,
            "start_day": str,
            "end_day": str,
        },
    },
    "ground_temperatures": {
        "metafields": {"number_of_ground_temperature_depths": int},
        "fields": {
            "depth": float,
            "soil_conductivity": float,
            "soil_density": float,
            "soil_specific_heat": float,
            "january": float,
            "february": float,
            "march": float,
            "april": float,
            "may": float,
            "june": float,
            "july": float,
            "august": float,
            "september": float,
            "october": float,
            "november": float,
            "december": float,
        },
    },
    "holidays_daylight_saving": {
        "metafields": {
            "leapyear_observed": str,
            "daylight_saving_start_day": str,
            "daylight_saving_end_day": str,
            "number_of_holidays": int,
        },
        "fields": {"holiday_name": str, "holiday_day": str},
    },
    "comments_1": {"metafields": {"comments_1": str}},
    "comments_2": {"metafields": {"comments_2": str}},
    "data_periods": {
        "metafields": {
            "number_of_data_periods": int,
            "number_of_records_per_hour": int,
        },
        "fields": {
            "data_period_name": str,
            "start_day_of_week": str,
            "start_day": str,
            "end_day": str,
        },
    },
    "data": {
        "fields": {
            "year": int,
            "month": int,
            "day": int,
            "hour": int,
            "minute": int,
            "data_source_and_uncertainty_flags": str,
            "dry_bulb_temperature": float,
            "dew_point_temperature": float,
            "relative_humidity": float,
            "atmospheric_station_pressure": float,
            "extraterrestrial_horizontal_radiation": float,
            "extraterrestrial_direct_normal_radiation": float,
            "horizontal_infrared_radiation_intensity": float,
            "global_horizontal_radiation": float,
            "direct_normal_radiation": float,
            "diffuse_horizontal_radiation": float,
            "global_horizontal_illuminance": float,
            "direct_normal_illuminance": float,
            "diffuse_horizontal_illuminance": float,
            "zenith_luminance": float,
            "wind_direction": float,
            "wind_speed": float,
            "total_sky_cover": float,
            "opaque_sky_cover": float,
            "visibility": float,
            "ceiling_height": float,
            "present_weather_observation": int,
            "present_weather_codes": str,
            "precipitable_water": float,
            "aerosol_optical_depth": float,
            "snow_depth": float,
            "days_since_last_snowfall": int,
            "albedo": float,
            "liquid_precipitation_depth": float,
            "liquid_precipitation_quantity": float,
        }
    },
}

_EPW_HEADER_NAMES: dict[str, str] = {
    "location": "LOCATION",
    "design_conditions": "DESIGN CONDITIONS",
    "typical_extreme_periods": "TYPICAL/EXTREME PERIODS",
    "ground_temperatures": "GROUND TEMPERATURES",
    "holidays_daylight_saving": "HOLIDAYS/DAYLIGHT SAVINGS",
    "comments_1": "COMMENTS 1",
    "comments_2": "COMMENTS 2",
    "data_periods": "DATA PERIODS",
}
