import warnings
import ssl
import requests
import pandas as pd  # pandas 임포트 추가
import streamlit as st
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import urllib3

# SSL 경고 숨기기 및 인증서 검증 비활성화
warnings.filterwarnings('ignore', category=urllib3.exceptions.InsecureRequestWarning)

class SSLAdapter(HTTPAdapter):
    """SSL 버전 설정을 위한 커스텀 HTTPAdapter"""
    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        # 기본 SSLContext 사용
        context = self.ssl_context or ssl.create_default_context()
        context.check_hostname = False  # check_hostname 비활성화
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

def get_weather_data(start_date, end_date):
    url = "https://apis.data.go.kr/1360000/VilageFcstInfoService/getVilageFcst"  # HTTPS를 사용

    params = {
        "serviceKey": Encoding_Key,
        "numOfRows": "10",
        "pageNo": "1",
        "dataType": "JSON",
        "base_date": start_date,
        "base_time": "0600",
        "nx": "60",
        "ny": "127",
    }

    try:
        # SSLContext를 사용하여 SSL 버전 설정
        # 여기서는 기본적으로 시스템에서 허용하는 최신 버전으로 설정됨
        context = ssl.create_default_context()
        context.check_hostname = False  # check_hostname 비활성화

        # Session을 이용한 요청
        session = requests.Session()
        adapter = SSLAdapter(ssl_context=context)
        session.mount("https://", adapter)

        # 요청 보내기
        response = session.get(url, params=params, verify=False, timeout=30)

        # 응답 상태 코드 확인
        response.raise_for_status()

        if response.status_code == 200:
            data = response.json()
            weather_data = data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
            if not weather_data:
                raise ValueError("날씨 데이터가 없습니다.")
            
            weather_df = pd.DataFrame(weather_data)
            weather_df['datetime'] = pd.to_datetime(weather_df['fcstDate'].astype(str) + ' ' + weather_df['fcstTime'].astype(str), format='%Y%m%d %H%M')
            return weather_df[['datetime', 'category', 'fcstValue']]
        else:
            raise ValueError(f"응답 코드 오류: {response.status_code}")

    except requests.exceptions.RequestException as e:
        st.error(f"기상청 API 호출 실패: {e}")
        st.write(f"API URL: {url}, 파라미터: {params}")
        st.write(f"상세 에러: {str(e)}")
    except Exception as e:
        st.error(f"오류 발생: {e}")
        st.write(f"API URL: {url}, 파라미터: {params}")

    return None

# 기상청 서비스 키를 변수로 선언
Encoding_Key = "5YGFViGmV1kbXqnD3qotA8CvXjxS4WEgX3nT0%2F0dF%2FlHZk2W7D%2FWgiCoBLNl3sbDbSR86pmOPLkr6AT4%2BRA2Jw%3D%3D"

def main():
    st.title('고속도로 교통량 예측 앱')

    # 기상청 데이터 가져오기
    today = pd.to_datetime('today').strftime('%Y%m%d')  # pandas가 정의되어야 합니다
    weather_data = get_weather_data(today, today)

    if weather_data is None:
        st.error("날씨 데이터를 가져오는데 실패했습니다.")
        return

    # 예시: 가져온 데이터 출력
    st.write(weather_data)

if __name__ == '__main__':
    main()
