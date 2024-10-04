from datetime import date, timedelta, datetime
from unittest.mock import patch, MagicMock

import pytest

from app.utils.datetime import get_datetime_utc_8, datetime_formatter


@patch("platform.system")
@patch("app.utils.datetime.datetime", new_callable=MagicMock(spec=datetime))
def test_get_datetime_utc_8(mock_datetime, mock_platform_system):
    # Arrange
    # Case 1: Linux
    fixed_datetime = datetime(2023, 10, 5, 12)
    mock_platform_system.return_value = "Linux"
    mock_datetime.now.return_value = fixed_datetime

    # Act
    dt = get_datetime_utc_8()

    # Assert
    assert dt == fixed_datetime + timedelta(hours=8)

    # Case 2: Windows
    mock_platform_system.return_value = "Windows"

    # Act
    dt = get_datetime_utc_8()

    # Assert
    assert dt == fixed_datetime


@pytest.mark.parametrize(
    "datetime_str, expected",
    [
        ("20231005", date(2023, 10, 5)),
        ("1121005", date(2023, 10, 5)),
        ("2023-10-05", date(2023, 10, 5)),
        ("112-10-05", date(2023, 10, 5)),
        ("2023/10/05", date(2023, 10, 5)),
        ("112/10/05", date(2023, 10, 5)),
        ("2023.10.05", date(2023, 10, 5)),
        ("112.10.05", date(2023, 10, 5)),
    ],
)
def test_datetime_formatter_with_valid_format(datetime_str, expected):
    # Act
    result = datetime_formatter(datetime_str)

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    "datetime_str, expected",
    [
        ("2023-13-01", ValueError),
        ("2023-00-01", ValueError),
        ("2023-01-32", ValueError),
        ("2023-01-00", ValueError),
        ("2023/13/01", ValueError),
        ("2023.13.01", ValueError),
        ("abcd-ef-gh", ValueError),
        ("2023-10", ValueError),
        ("202310", ValueError),
    ],
)
def test_datetime_formatter_with_invalid_format(datetime_str, expected):
    # Act
    with pytest.raises(expected):
        datetime_formatter(datetime_str)
