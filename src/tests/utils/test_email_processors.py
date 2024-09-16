import pickle
from unittest.mock import patch, mock_open

import pytest
from google.oauth2.credentials import Credentials

from app.utils.email_processors import GmailProcessor


# Mock class to simulate the class containing _get_credentials_instance
class MockGmailProcessorClass:
    def __init__(self, token_file):
        self.token_file = token_file

    _get_credentials_instance = GmailProcessor._get_credentials_instance


@pytest.mark.parametrize(
    "token_file_content",
    [
        pickle.dumps(Credentials(token='its-a-token-to-everyone')),
    ],
    ids=[
        "valid_credentials",
    ]
)
def test_get_credentials_instance_valid_credentials(token_file_content):
    # Arrange
    token_file_path = 'test_token_file'
    mock_instance = MockGmailProcessorClass(token_file_path)
    m_open = mock_open(read_data=token_file_content)

    with patch('builtins.open', m_open), patch('os.path.exists', return_value=token_file_content is not None):
        # Act
        creds = mock_instance._get_credentials_instance()

        # Assert
        assert isinstance(creds, Credentials)


@pytest.mark.parametrize(
    "token_file_content, expected_exception, expected_message",
    [
        # Edge case: token file does not exist
        (None, FileNotFoundError, 'No token file found at {token_file_path}'),
    ],
    ids=[
        "file_not_found",
    ]
)
def test_get_credentials_instance(token_file_content, expected_exception, expected_message):
    # Arrange
    token_file_path = 'test_token_file'
    mock_instance = MockGmailProcessorClass(token_file_path)

    m_open = mock_open()
    m_open.side_effect = FileNotFoundError

    with patch('builtins.open', m_open), patch('os.path.exists', return_value=token_file_content is not None):
        # Act
        with pytest.raises(expected_exception) as exc_info:
            mock_instance._get_credentials_instance()

        # Assert
        assert str(exc_info.value) == expected_message.format(token_file_path=token_file_path)



@pytest.mark.parametrize(
    "token_file_content, expected_exception, expected_message",
    [
        # Happy path
        (pickle.dumps(Credentials(token='its-a-token-to-everyone')), None, None),

        # Edge case: token file does not exist
        (None, FileNotFoundError, 'No token file found at non_existent_file'),

        # Error case: token file contains invalid data
        (pickle.dumps("invalid_data"), TypeError, "Expected Credentials instance, got <class 'str'>"),
    ],
    ids=[
        "valid_credentials",
        "file_not_found",
        "invalid_credentials_type",
    ]
)
def test_get_credentials_instance_by_file_not_found(token_file_content, expected_exception, expected_message):
    # Arrange
    token_file_path = 'test_token_file'
    mock_instance = MockGmailProcessorClass(token_file_path)

    if token_file_content is not None:
        m_open = mock_open(read_data=token_file_content)
    else:
        m_open = mock_open()
        m_open.side_effect = FileNotFoundError

    with patch('builtins.open', m_open), patch('os.path.exists', return_value=token_file_content is not None):

        # Act
        if expected_exception:
            with pytest.raises(expected_exception) as exc_info:
                mock_instance._get_credentials_instance()

            # Assert
            assert str(exc_info.value) == expected_message
        else:
            creds = mock_instance._get_credentials_instance()

            # Assert
            assert isinstance(creds, Credentials)


@pytest.mark.parametrize(
    "token_file_content, expected_exception, expected_message",
    [
        # Error case: token file contains invalid data
        (pickle.dumps("invalid_data"), TypeError, "Expected Credentials instance, got {type}"),
    ],
    ids=[
        "invalid_credentials_type",
    ]
)
def test_get_credentials_instance_by_invalid_credentials_type(token_file_content, expected_exception, expected_message):
    # Arrange
    token_file_path = 'test_token_file'
    mock_instance = MockGmailProcessorClass(token_file_path)
    m_open = mock_open(read_data=token_file_content)

    with patch('builtins.open', m_open), patch('os.path.exists', return_value=token_file_content is not None):
        # Act
        with pytest.raises(expected_exception) as exc_info:
            mock_instance._get_credentials_instance()

        # Assert
        assert str(exc_info.value) == expected_message.format(type=type(pickle.loads(token_file_content)))
