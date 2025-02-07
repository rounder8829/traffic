import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import ssl

class TLSAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)

def get_weather_data(base_date, base_time, nx, ny):
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    params = {
        'serviceKey': st.secrets["API_KEY"],
        'numOfRows': '100',
        'pageNo': '1',
        'dataType': 'XML',
        'base_date': base_date,
        'base_time': base_time,
        'nx': str(nx),
        'ny': str(ny)
    }

    try:
        session = requests.Session()
        session.mount('https://', TLSAdapter())
        response = session.get(url, params=params, timeout=10)
        response.raise_for_status()

        # 응답 내용 확인
        st.write("API 응답:", response.content)

        # XML 파싱
        root = ET.fromstring(response.content)
        items = root.findall('.//item')
        
        if items:
            return [item.attrib for item in items]
        else:
            st.error("API 응답에 날씨 데이터가 없습니다.")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"API 호출 오류: {e}")
        return None
    except ET.ParseError as e:
        st.error(f"XML 파싱 오류: {e}")
        st.error(f"응답 내용: {response.content}")
        return None


def predict_highway_traffic(weather_data, highway_data):
    if not weather_data or not highway_data:
        return "예상 교통량을 알 수 없습니다."
    
    weather_df = pd.DataFrame(weather_data)

    try:
        temperature = float(weather_df.loc[weather_df['category'] == 'T1H', 'fcstValue'].values[0])
        rain = float(weather_df.loc[weather_df['category'] == 'RN1', 'fcstValue'].values[0])
        wind_speed = float(weather_df.loc[weather_df['category'] == 'WSD', 'fcstValue'].values[0])

        highway_traffic = highway_data.get('traffic', 0)

        # 날씨에 따른 교통량 예측
        if rain > 5:
            return f"비로 인해 교통량 증가 예상 (현재 교통량: {highway_traffic + 100}대)"
        elif wind_speed > 10:
            return f"강풍으로 인해 교통량 감소 예상 (현재 교통량: {highway_traffic - 50}대)"
        elif temperature > 30:
            return f"더위로 인해 교통량 증가 예상 (현재 교통량: {highway_traffic + 200}대)"
        elif temperature < 10:
            return f"추위로 인해 교통량 감소 예상 (현재 교통량: {highway_traffic - 100}대)"
        else:
            return f"교통량 정상 예상 (현재 교통량: {highway_traffic}대)"
    except (IndexError, ValueError):
        return "기상 데이터 처리 오류 발생"

st.title("고속도로 교통량 예측 앱")

# 현재 날짜와 시간을 기반으로 base_date와 base_time을 설정
current_datetime = datetime.now()
base_date = current_datetime.strftime('%Y%m%d')
base_time = (current_datetime - timedelta(hours=1)).strftime('%H00')

# 고속도로 좌표 매핑
highway_coords = {
    "서울 고속도로 1번": (60, 127),
    "부산 고속도로 2번": (98, 76),
    "대구 고속도로 3번": (89, 79),
    "대전 고속도로 4번": (93, 95),
    "광주 고속도로 5번": (97, 92)
}

# 고속도로 선택
highway = st.sidebar.selectbox("고속도로 구간 선택", list(highway_coords.keys()))
nx, ny = highway_coords[highway]

# 예시 교통 데이터 (실제 데이터로 대체 필요)
highway_data = {
    "traffic": 1500  # 예시 교통량
}

# 날씨 데이터 가져오기
weather_data = get_weather_data(base_date, base_time, nx, ny)

if weather_data:
    st.write("날씨 데이터:")
    st.json(weather_data)
else:
    st.error("날씨 데이터를 가져오는데 실패했습니다.")

# 교통량 예측
traffic_prediction = predict_highway_traffic(weather_data, highway_data)

if traffic_prediction:
    st.write(f"예상 교통량: {traffic_prediction}")
else:
    st.write("교통량 예측을 할 수 없습니다.")

# 사이드바 설정
st.sidebar.header("교통량 예측을 위한 설정")
time_of_day = st.sidebar.radio("시간대 선택", ["오전", "오후"])

st.sidebar.write(f"선택된 고속도로 구간: {highway}")
st.sidebar.write(f"선택된 시간대: {time_of_day}")

if highway and time_of_day:
    st.write(f"{highway}에서 {time_of_day}에 예상되는 교통량은 {traffic_prediction}입니다.")

# 예측 결과 테이블 표시
prediction_df = pd.DataFrame({
    '고속도로 구간': [highway],
    '시간대': [time_of_day],
    '예상 교통량': [traffic_prediction]
})

st.write("고속도로 교통량 예측 결과:")
st.dataframe(prediction_df)
