import base64
import os
import pickle
import tempfile
from abc import abstractmethod, ABC
from os.path import join as path_join
from typing import List, Union

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from pydantic import BaseModel

from app.core.enums import GmailScopes, FileTypes
from app.utils.file_processors import DocumentProcessor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIAL_DIR = os.path.join(BASE_DIR, 'credentials')

# Gmail scopes
SCOPES = [
    GmailScopes.READ_ONLY,
    GmailScopes.SEND,
]


def get_gmail_service() -> Resource:
    creds = None
    token_path = path_join(CREDENTIAL_DIR, 'token.pickle')

    # Load the previously stored credentials
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    # if there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                path_join(CREDENTIAL_DIR, 'credentials.json'), SCOPES)
            creds = flow.run_local_server(port=0)

        # save the credentials for the next run
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)


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

    def search(self, keyword: str, file_type: Union[FileTypes, None] = None) -> List[dict]:
        results = self.service.users().messages().list(userId='me', q=keyword).execute()
        messages = results.get('messages', [])
        emails = []

        for message in messages:
            msg = self.service.users().messages().get(userId='me', id=message['id']).execute()
            email = {
                'id': msg['id'],
                'subject': next(header['value'] for header in msg['payload']['headers'] if header['name'] == 'Subject')
            }

            if file_type is not None:
                email['has_file'] = any(
                    part['filename'].lower().endswith(f'.{file_type}')
                    for part in msg['payload'].get('parts', [])
                    if 'filename' in part
                )

            emails.append(email)

        return emails


class GmailEmailProcessor(EmailProcessor):
    def __init__(self, document_processor: DocumentProcessor):
        self.document_processor = document_processor
        self.service = get_gmail_service()
        self.searcher = GmailSearcher(self.service)

    def process(self, keyword: str) -> List[dict]:
        emails = self.searcher.search(keyword, self.document_processor.file_type)
        results = []

        for email in emails:
            file_content = None

            if email.get('has_file'):
                file_content = self._process_file_attachment(email['id'], keyword)
            results.append({
                'subject': email['subject'],
                'file_content': file_content
            })

        return results

    def _process_file_attachment(self, email_id: str, keyword: str) -> Union[str, None]:
        message = self.service.users().messages().get(userId='me', id=email_id).execute()

        for part in message['payload'].get('parts', []):
            if (
                    part['filename'].lower().endswith(f'.{self.document_processor.file_type}')
                    and ('body' in part and 'attachmentId' in part['body'])
            ):
                attachment = self.service.users().messages().attachments().get(
                    userId='me', messageId=email_id, id=part['body']['attachmentId']
                ).execute()
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
        return None


class SearchRequest(BaseModel):
    keyword: str


class SendEmailRequest(BaseModel):
    to: str
    subject: str
    body: str
