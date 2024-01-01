from requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import pandas as pd
import io

# 전체 출력 활성화
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

# Google Drive API 사용을 위한 인증 정보 로드 또는 생성
creds = None
token_path = "token.json"

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        # OAuth 클라이언트 ID와 시크릿이 있는 파일의 경로
        client_secrets_path = "client_secret.json"
        
        # 사용자에게 요청할 권한 범위
        scopes = [
            "https://www.googleapis.com/auth/drive.readonly"
        ]
        
        # Google Auth Flow 생성
        flow = InstalledAppFlow.from_client_secrets_file(
            client_secrets_path, scopes=scopes
        )
        creds = flow.run_local_server(port=0)
        
        # 획득한 권한을 저장
        with open(token_path, "w") as token:
            token.write(creds.to_json())

# Google Drive API 빌드
drive_service = build("drive", "v3", credentials=creds)

# Google Drive에서 특정 문서의 ID 얻어오기(공유 가능한 링크에서 ID 추출)
file_id = "Google Drive에서 불러올 문서 ID"

# 파일 다운로드
request = drive_service.files().export_media(fileId=file_id, mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
file_stream = io.BytesIO()
downloader = MediaIoBaseDownload(file_stream, request)

done = False
while done is False:
    _, done = downloader.next_chunk()

# 파일을 바이트 스트림으로 열어서 pandas로 읽어오기
df = pd.read_excel(file_stream)

# 데이터프레임 출력
print(df)
