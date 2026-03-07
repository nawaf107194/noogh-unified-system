import pytest
from unittest.mock import patch, MagicMock
from src.scripts.train_time_series_predictor import main

@patch('src.scripts.train_time_series_predictor.get_metrics_collector')
@patch('src.scripts.train_time_series_predictor.convert_to_metrics_data')
class TestMain:

    def test_happy_path(self, mock_convert, mock_get):
        # Mocks setup
        args = MagicMock(hours=168)
        mock_get.return_value = [{} for _ in range(1001)]
        mock_convert.return_value = []

        # Run the function
        result = main()

        # Assertions
        assert result == 0
        mock_get.assert_called_once_with()
        mock_convert.assert_called_once_with(mock_get.return_value)
        # Add more specific assertions as needed

    def test_empty_data(self, mock_convert, mock_get):
        # Mocks setup
        args = MagicMock(hours=168)
        mock_get.return_value = []
        mock_convert.return_value = []

        # Run the function
        result = main()

        # Assertions
        assert result == 1
        mock_get.assert_called_once_with()
        mock_convert.assert_not_called()

    def test_invalid_hours(self, mock_convert, mock_get):
        # Mocks setup
        args = MagicMock(hours=5)
        mock_get.return_value = [{} for _ in range(1001)]
        mock_convert.return_value = []

        # Run the function
        result = main()

        # Assertions
        assert result == 1
        mock_get.assert_called_once_with()
        mock_convert.assert_not_called()

    def test_invalid_model_type(self, mock_convert, mock_get):
        # Mocks setup
        args = MagicMock(hours=168)
        args.model_type = 'Foo'
        mock_get.return_value = [{} for _ in range(1001)]
        mock_convert.return_value = []

        # Run the function
        result = main()

        # Assertions
        assert result == 1
        mock_get.assert_called_once_with()
        mock_convert.assert_not_called()