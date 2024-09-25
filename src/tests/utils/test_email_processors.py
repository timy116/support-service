from unittest.mock import Mock, patch, mock_open, PropertyMock

import pytest
from google.oauth2.credentials import Credentials

from app.utils.email_processors import GmailProcessor, SCOPES


@patch('pickle.load')
@patch('app.utils.email_processors.open', new_callable=mock_open, read_data=b"token_file_content")
@patch('app.utils.email_processors.exists')
@patch('app.utils.email_processors.GmailSearcher', new_callable=Mock)
@patch('app.utils.email_processors.DocumentProcessor', new_callable=Mock)
def test_get_credentials_instance_valid_credentials(
        mock_document_processor, mock_searcher, mock_path_exists, mock_built_open, mock_pickle_load
):
    # Arrange
    creds = Mock(Credentials)
    processor = GmailProcessor(mock_document_processor, mock_searcher)
    processor.credentials_file = 'path/to/credentials.json'
    processor.token_file = 'path/to/token.pickle'
    mock_path_exists.return_value = True
    mock_pickle_load.return_value = creds

    # case 1: valid credentials
    credentials = processor.credentials

    # Assert
    mock_path_exists.assert_called_once_with(processor.token_file)
    mock_built_open.assert_called_once_with(processor.token_file, 'rb')
    mock_pickle_load.assert_called_once_with(mock_built_open())
    assert credentials == creds

    # case 2: token file does not exist
    processor._credentials = None
    mock_path_exists.return_value = False
    assert processor.credentials is None

    # case 3: invalid credentials type
    mock_path_exists.return_value = True
    mock_pickle_load.return_value = "invalid_data"

    # Assert
    with pytest.raises(TypeError):
        credentials = processor.credentials

        assert credentials is None


@patch('app.utils.email_processors.GmailSearcher', new_callable=Mock)
@patch('app.utils.email_processors.DocumentProcessor', new_callable=Mock)
@patch('app.utils.email_processors.GmailProcessor.credentials', new_callable=PropertyMock)
@patch('app.utils.email_processors.InstalledAppFlow.from_client_secrets_file')
@patch('app.utils.email_processors.build')
@patch('app.utils.email_processors.open', new_callable=mock_open, read_data=b"token_file_content")
@patch('pickle.dump')
def test_service_property(
        mock_pickle_dump,
        mock_built_open,
        mock_build,
        mock_from_client_secrets_file,
        mock_credentials,
        mock_document_processor,
        mock_searcher
):
    # Arrange
    processor = GmailProcessor(mock_document_processor, mock_searcher)
    processor.credentials_file = 'path/to/credentials.json'
    processor.token_file = 'path/to/token.pickle'
    mock_creds = Mock()
    mock_credentials.return_value = mock_creds

    # case 1: valid credentials
    mock_creds.valid = True
    service = processor.service

    # Assert
    assert service == mock_build.return_value
    assert processor._service is not None
    mock_build.assert_called_once_with('gmail', 'v1', credentials=mock_creds)
    mock_from_client_secrets_file.assert_not_called()

    # case 2: credentials expired, refresh token exists
    processor._service = None
    mock_build.reset_mock()
    mock_creds.valid = False
    mock_creds.expired = True
    mock_creds.refresh_token = 'refresh_token'
    service = processor.service

    # Assert
    mock_built_open.assert_called_once_with(processor.token_file, 'wb')
    assert service == mock_build.return_value
    mock_creds.refresh.assert_called_once()
    mock_pickle_dump.assert_called_once()
    mock_from_client_secrets_file.assert_not_called()

    # case 3: no credentials, user login required
    processor._service = None
    mock_build.reset_mock()
    mock_creds.valid = False
    mock_creds.expired = False
    mock_creds.refresh_token = None
    mock_new_creds = Mock()
    mock_flow = Mock()
    mock_from_client_secrets_file.return_value = mock_flow
    mock_flow.run_local_server.return_value = mock_new_creds
    service = processor.service

    # Assert
    assert service == mock_build.return_value
    mock_from_client_secrets_file.assert_called_once_with(processor.credentials_file, SCOPES)
    mock_flow.run_local_server.assert_called_once_with(port=0)
    mock_build.assert_called_once_with('gmail', 'v1', credentials=mock_new_creds)
