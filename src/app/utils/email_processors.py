import base64
import os
import pickle
import tempfile
from abc import abstractmethod, ABC
from os.path import join as path_join, exists
from typing import List, Union, Type

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from structlog import get_logger, BoundLogger

from app.core.enums import GmailScopes, FileTypes
from app.utils.file_processors import DocumentProcessor

# Logger
logger: BoundLogger = get_logger()

# Directory and file names
CREDENTIALS_DIR_NAME = 'credentials'
TOKEN_FILE_NAME = 'token.pickle'
CREDENTIALS_JSON_FILE_NAME = 'credentials.json'

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIAL_DIR = os.path.join(BASE_DIR, CREDENTIALS_DIR_NAME)

# Gmail scopes
SCOPES = [
    GmailScopes.READ_ONLY,
    GmailScopes.SEND,
]


class EmailSearcher(ABC):
    @abstractmethod
    def search(self, keyword: str) -> List[dict]:
        pass


class EmailProcessor(ABC):
    @abstractmethod
    def process(self, keyword: str) -> List[dict]:
        pass


class GmailSearcher(EmailSearcher):
    def __init__(self, service: Resource):
        self.service = service

    def search(self, keyword: str, file_type: Union[FileTypes, None] = None) -> List[dict[str, Union[str, bool]]]:
        raise NotImplementedError('Method search must be implemented')


class GmailDailyReportSearcher(GmailSearcher):

    def search(self, keyword: str, file_type: Union[FileTypes, None] = None) -> List[dict[str, Union[str, bool]]]:
        results = self.service.users().messages().list(userId='me', q=keyword).execute()
        messages = results.get('messages', [])
        emails = []

        for message in messages:
            msg = self.service.users().messages().get(userId='me', id=message['id']).execute()
            email = {
                'id': msg['id'],
                'subject': next(header['value'] for header in msg['payload']['headers'] if header['name'] == 'Subject')
            }

            # Check if the email subject is the same as the keyword
            if email["subject"] != keyword or email["subject"].find(keyword) == -1:
                continue

            if file_type is not None:
                email['has_file'] = any(
                    part['filename'].lower().endswith(f'.{file_type}')
                    for part in msg['payload'].get('parts', [])
                    if 'filename' in part
                )

            emails.append(email)

            # If the search is for a daily report, only the first email is needed
            if len(emails) == 1:
                break

        return emails


class GmailProcessor(EmailProcessor):
    def __init__(
            self,
            document_processor: Union[DocumentProcessor, None] = None,
            searcher: Union[Type[GmailSearcher] | Type[GmailDailyReportSearcher], None] = None
    ):
        self._credentials = None
        self._service = None
        self._searcher = None
        self.document_processor = document_processor
        self.token_file = path_join(CREDENTIAL_DIR, TOKEN_FILE_NAME)
        self.credentials_file = path_join(CREDENTIAL_DIR, CREDENTIALS_JSON_FILE_NAME)
        self.searcher_class = searcher

    @property
    def credentials(self) -> Union[Credentials, None]:
        try:
            if self._credentials is None:
                if not exists(self.token_file):
                    return self._credentials

                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)

                    if not isinstance(creds, Credentials):
                        raise TypeError(f'Expected Credentials instance, got {type(creds)}')

                self._credentials = creds
        except Exception as e:
            logger.exception('Failed to get credentials instance')
            raise e

        return self._credentials

    @property
    def service(self) -> Resource:
        try:
            if self._service is None:
                creds = self.credentials

                # if there are no (valid) credentials available, let the user log in
                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                    else:
                        flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                        creds = flow.run_local_server(port=0)

                    # save the credentials for the next run
                    with open(self.token_file, 'wb') as token:
                        pickle.dump(creds, token)

                    self._credentials = creds

                self._service = build('gmail', 'v1', credentials=creds)
        except Exception as e:
            logger.exception('Failed to get Gmail service')
            raise e

        return self._service

    @property
    def searcher(self) -> Union[GmailSearcher, GmailDailyReportSearcher]:
        if self._searcher is None:
            self._searcher = self.searcher_class(self.service)

        return self._searcher

    def process(self, keyword: str) -> List[Union[list[dict[str, str | float]], str]]:
        if not keyword:
            return []

        emails = self.searcher.search(keyword, self.document_processor.file_type)
        results = []

        for email in emails:
            if email.get('has_file'):
                if result := self._process_file_attachment(email['id'], keyword):
                    results.append(result)

            if isinstance(self.searcher, GmailDailyReportSearcher):
                break

        return results

    def _get_attachment(self, email_id: str):
        message = self.service.users().messages().get(userId='me', id=email_id).execute()

        for part in message['payload'].get('parts', []):
            if (
                    part['filename'].lower().endswith(f'.{self.document_processor.file_type}')
                    and ('body' in part and 'attachmentId' in part['body'])
            ):
                return self.service.users().messages().attachments().get(
                    userId='me', messageId=email_id, id=part['body']['attachmentId']
                ).execute()

    def _process_file_attachment(self, email_id: str, keyword: str) -> Union[list, str]:
        attachment = self._get_attachment(email_id)
        file_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))

        with tempfile.NamedTemporaryFile(
                delete=False,
                prefix=f'{keyword}_',
                suffix=f'.{self.document_processor.file_type}'
        ) as temp_file:
            temp_file.write(file_data)
            temp_file_path = temp_file.name
        try:
            return self.document_processor.process(temp_file_path)
        finally:
            # remove the temporary file
            os.unlink(temp_file_path)
