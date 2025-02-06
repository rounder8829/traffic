import streamlit as st
import pandas as pd
import requests
from prophet import Prophet


# 기상청 API 호출 함수
# Encoding 인증키 사용
ENCODE_KEY = "5YGFViGmV1kbXqnD3qotA8CvXjxS4WEgX3nT0%2F0dF%2FlHZk2W7D%2FWgiCoBLNl3sbDbSR86pmOPLkr6AT4%2BRA2Jw%3D%3D"


def get_weather_data(statr_date, end_date) :
    url = f"https://apis.data.go.kr/1360000/VilageFcstInfoService/getVilageFcst"

    
    params = {
        "serviceKey" : ENCODE_KEY, # Encoding 인증키
        "numOfRows" : "10",        # 한 번에 받을 데이터 수
        "pageNo" : "1",            # 페이지 번호
        "dateType" : "JSON",       # 응답 데이터 형식 (JSON)
        "base_date" : statr_date,  # 시작 날짜(YYYYMMDD 형식)
        "base_time" : "0600",      # 기준 시간(예: 0600 => 오전 6시)
        "nx" : "60",               # 예시 좌표 (경도)
        "ny" : "127",              # 예시 좌표 (위도)
    }


    response = requests.get(url, params=params)
    # requests.get(): HTTP GET 요청을 보내는 함수. 기상청에 API 요청을 보낸다.
        # url: 요청할 API 의 URL
        # params=params: params 는 API에 전달할 쿼리 파라미터를 포함하는 딕셔너리이다.
            # 인증키, 날짜, 위치 등의 정보가 들어있다.
    

    if response.status_code == 200 :
    # response.status_code: 코드라인 요청에 대한 응답 상태코드가 200인지 확인.
    # 200 이면 성공!

        data = response.json()
        # response.json(): API 로 부터 받은 응답을 JSON 형식으로 변환하여
        # Python 객체(딕셔너리 등) 으로 반환한다
        # 기상청 API의 응답을 JSON 형식으로 변환하여 data 변수에 저장한다

        weather_data = data['response']['body']['items']['item']
        # 기상청 API에서 제공하는 응답 구조에 맞춰 필요한 데이터를 추출
        # data['response']['body']['items']['item']:
            # response > body > items > item 키에 해당하는 값을 추출하며
            # API 응답의 구체적인 데이터가 있는 위치를 나타낸다.
        # weather_data: 기상청 API 에서 가져온 날씨 데이터를 가지고 있다.

        weather_df = pd.DataFrame(weather_data)
        # pd.DataFrame(): 가져온 날씨 데이터를 Pandas DataFrame 형식으로 변환하여
        # weather_df 변수에 저장한다.

        return weather_df
        # 날씨 데이터를 DataFrame 으로 변환한 후 이를 반환한다.
        # 함수에서 호출한 곳으로 전달되어 후속 작업을 진행하도록 해준다.

    else :
        st.error("기상청 API 호출 실패")
        return None
    # st.error: 요청이 실패(상태코드가 200이 아닌 경우) 하면
        # Streamlit 라이브러리 함수로 사용자에게 오류메시지를 화면에 표시한다
        # API 호출 실패 시 사용자에게 알려주는 메시지를 표시하는 것.
    # return None: API 호출 실패 시 None 을 반환하는데 실패를 의미한다.



# 고속도로 교통량 데이터 불러오기
def load_traffic_data() :
    # 교통량 데이터 파일경로
    highway_data = pd.read_csv('data/ETC_P7_07_04_516342.csv')

    # 날짜 형식으로 변환
    highway_data['datetime'] = pd.to_datetime(highway_data['날짜컬럼'])

    # 필요한 컬럼만 선택한다
    highway_data = highway_data[['datetime', '교통량']]
    return highway_data


# Prophet 모델을 학습하고 예측하는 함수
def train_and_predict(model_data) :
    model = Prophet()

    # 기온을 regressor 로 추가
    model.add_regressor('온도')

    # 풍량을 regressor 로 추가
    model.add_regressor('풍량')

    # 강수량을 regressor 로 추가
    model.add_regressor('강수량')


    model.fit(model_data)
    future = model.make_future_dataframe(model_data, periods= 7)
    forecast = model.predict(future)

    return forecast



def main() :
    
    st.title('고속도로 교통량 예측 앱')


    # 기상청 데이터 가져오기
    today = pd.to_datetime('today').strftime('%Y%m%d')
    weather_data = get_weather_data(today, today)


    # 교통량 데이터 불러오기
    highway_data = load_traffic_data()


    # 기상청 데이터와 교통량 데이터를 병합
    merged_data = pd.merge(weather_data, highway_data, on='datetime', how='left')


    # Prophet 모델 학습 및 예측
    forecast = train_and_predict(merged_data)


    # 예측 결과 시각화
    st.write("예측된 교통량")
    st.line_chart(forecast['yhat'])


    # 예측된 교통량 출력
    st.write(forecast.tail(7)[['ds', 'yhat']])


if __name__ == '__main()__' :
    main()






