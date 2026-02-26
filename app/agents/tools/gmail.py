"""Gmail Tool - LangChain 공식 GmailToolkit 사용"""
from pathlib import Path

from langchain_google_community import GmailToolkit
from langchain_google_community._utils import get_google_credentials
from langchain_google_community.gmail.utils import (
    build_gmail_service,
)

ROOT = Path(__file__).parent.parent.parent.parent

def get_gmail_tools() -> list:
    """
    Gmail 툴킷에서 툴 리스트 반환.

    Returns:
        [GmailCreateDraft, GmailSendMessage, GmailSearch, GmailGetMessage, GmailGetThread]

    Setup:
        1. Google Cloud Console에서 OAuth 2.0 credentials.json 다운로드
        2. 첫 실행 시 브라우저 인증 → token.json 자동 생성
    """
    credentials = get_google_credentials(
        token_file=str(ROOT / "secret" / "gmail_token.json"),
        scopes=["https://mail.google.com/"],
        client_secrets_file=str(ROOT / "secret" / "gmail_credentials.json"),
    )
    api_resource = build_gmail_service(credentials=credentials)
    toolkit = GmailToolkit(api_resource=api_resource)

    return toolkit.get_tools()
