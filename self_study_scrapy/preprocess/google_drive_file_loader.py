"""Google API 사용해서 문서 불러오기"""
from requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import pandas as pd
import io
import json

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
        client_secrets_path = "preprocess/client_secret.json"
        
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
file_id = "199hLJh2LsAOdgN-Y5pqzAxBYhCZkMJqbMfMjZOHoOX4"

# 파일 다운로드
request = drive_service.files().export_media(fileId=file_id, mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
file_stream = io.BytesIO()
downloader = MediaIoBaseDownload(file_stream, request)

done = False
while done is False:
    _, done = downloader.next_chunk()

# 바이트 스트림에서 데이터프레임으로 읽어오기
df = pd.read_excel(file_stream)

"""media_list_file 전처리"""
"""기존 언론사 항목 수정"""
df = df[:65] # 보류 데이터 제외하고 불러오기
df.drop([0], axis=0, inplace=True) # 0행 제거

# 카테고리 열 이름 변경
df.rename(columns={"핀인사이트(=네이버)":"핀인사이트 category", "Unnamed: 1":"핀인사이트 category_sub", "네이트":"네이트 category", "Unnamed: 3":"네이트 category_sub"}, inplace=True)

# 핀인사이트 결측치 채우기
df["핀인사이트 category"].fillna(method="ffill", inplace=True)
df["핀인사이트 category_sub"].fillna("", inplace=True)

# 네이트 결측치 채우기
df["네이트 category"].fillna(method="ffill", inplace=True)
df["네이트 category_sub"].fillna("", inplace=True)
df["네이트 category"] = df["네이트 category"].replace("-", "")

"""새로운 언론사 항목 수정"""
# 새로운 언론사 리스트 생성
new_media_list = list(df.columns)[4:]

for new_media in new_media_list:
    df[f"{new_media}"].fillna("", inplace=True) # 새로운 언론사의 결측치를 ""로 변경
    df[f"{new_media}"] = df[f"{new_media}"].replace(" - ", "-", regex=True).replace("- ", "-", regex=True).replace(", ", ",", regex=True) # 새로운 언론사의 입력 형태 통일    

# 데이터프레임을 JSON 파일로 저장
with open("preprocess/google_drive_media_list_file.json", "w", encoding="utf-8") as json_file:
    # 쉼표 추가: lines=True로 설정하여 라인마다 객체를 쉼표로 구분
    df_json = df.to_dict(orient="records")
    json.dump(df_json, json_file, indent=2, ensure_ascii=False)
