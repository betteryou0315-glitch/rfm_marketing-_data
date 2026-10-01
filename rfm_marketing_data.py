#주제: RFM 지표 만들기
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

online_retail = pd.read_csv("online_retail.csv")

#print(online_retail.info()) #info 메서드 : 전체적인 데이터 구조 파악

online_retail = online_retail.dropna(subset=['CustomerID']) 
#dropna 의 subset 을 쓰면 그 컬럼 값의 결측값만 제거할 수 있다
#cutomer id 의 결측값은 데이터 사용에 무의미 함으로 제거

online_retail = online_retail[~(online_retail['InvoiceNo'].str.startswith('C'))] 
#Invoice NO 컬럼에서 단어가 C 가 아닌걸로 시작하는 것만 출력
#C로 시작하는 행은 취소 주문인데 , 취소주문까지 포함해서 계산하면 RFM 계산이 왜곡됨
#그래서 C로 시작하지 않는 행만 남겨서 정상적인 거래만 포함시킴

online_retail['InvoiceDate'] = pd.to_datetime(online_retail['InvoiceDate'])
#invoice date 컬럼이 문자 컬럼이라 , 최근 구매일이 언제인지 같은 경우를 구할 수 없음
#그래서 pd.to_datetime 으로 날짜형으로 바꿔줌

online_retail['Total_price'] = online_retail['Quantity'] * online_retail['UnitPrice']
#RFM 에서 M을 계산하기 위해 컬럼을 만듬
#원래 데이터에서는 금액 자체가 없어서 양 x 단가로 계산

recently_date = online_retail['InvoiceDate'].max()
# R 지표를 만들기 위해 최근 날짜를 구한다(기준일)

last_date = online_retail.groupby('CustomerID')['InvoiceDate'].max()
#고객별 최근 구매일 

time = recently_date - last_date
Recency = time.dt.days
#R지표 계산하기 : 기준일 - 고객별 최근 구매일
#날짜끼리 뺀다면 timedelta 라는 값이 나오는데 몇일 , 몇시간 , 몇분이 담김
# 그러나 우리는 일 수만 필요함으로 df.days 는 일수만 뽑아준다

Frequency = online_retail.groupby('CustomerID')['InvoiceNo'].nunique()
#nunique 매서드는 중복을 제거하고 고유값을 계산하게 도와준다
#고객별 "구매횟수" 를 구한다 , F 지표만들기

Monetary = online_retail.groupby('CustomerID')['Total_price'].sum()
# M 지표 만들기

rfm = {'Recency' : Recency ,
       'Frequency' : Frequency , 
       'Monetary' : Monetary}
#만든 지표들을 하나로 합치기 위해 , 딕셔너리로 만든다
#dataframe 은 딕셔너리의 키 값을 컬럼 값으로 지정해주기 때문에

rfm_indicator = pd.DataFrame(rfm)

f_score = pd.qcut(rfm_indicator['Frequency'] ,labels=[1,2,3,4] , q=5 ,duplicates='drop')
#duplicates 는 중복된 경계를 자동으로 합쳐준다(값이 한쪽으로 몰려있을 경우 사용)
#좋은 고객 과 나쁜 고객을 구별하기 위해 등급을 나눈다
#등급을 매기기 위해서 pd.qcut 을 이용한다

r_score = pd.qcut(rfm_indicator['Recency'] , labels=[5,4,3,2,1] , q = 5)
#F 와 M 과 점수 반대 , F 와 M 은 점수가 높을 수록 좋지만
#최근 구매일은 숫자가 작을수록 좋으니

m_score = pd.qcut(rfm_indicator['Monetary'] , labels=[1,2,3,4,5] , q = 5 , duplicates='drop')

rfm_indicator['R_score'] = r_score
rfm_indicator['F_score'] = f_score
rfm_indicator['M_score'] = m_score


rfm_indicator['rfm_score'] = rfm_indicator['R_score'].astype(int) + rfm_indicator['F_score'].astype(int) + rfm_indicator['M_score'].astype(int)
#총점으로 고객등급을 나누기 위해서 스코어를 다 더해준다
#qcut 은 범주형임으로 덧셈이 안됨 그래서 정수형으로 바꿔주는 astype 이용 

bins = [0,4,7,11,14]
labels = ['이탈위험' , '일반고객' , '우수고객' , 'VIP']
rfm_indicator['Segment'] = pd.cut(rfm_indicator['rfm_score'] , bins = bins , labels=labels)
#등급 이름 붙이기 
#이름을 직접 붙이기 위해 cut 매서드 이용

segment_counts = rfm_indicator['Segment'].value_counts()

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

sns.barplot(x = segment_counts.index , y = segment_counts.values)
plt.show()

#정리

#1
#"VIP(877명)와 우수고객(1276명)을 합치면 전체의 약 49%로, 
# 절반 가까운 고객이 활발하게 구매하는 고가치 고객이다. 이탈위험군(795명)보다 VIP가 더 많다는 건 
# 이 쇼핑몰이 신규 고객을 충성 고객으로 잘 전환시키고 있다는 신호로 볼 수 있다."

#2
#"만약 구매 횟수(Frequency)만으로 고객 가치를 판단했다면, 12346.0 고객(1번 구매)은 최하위로 분류됐을 것이다. "
#"하지만 실제로는 한 번에 77,183원이라는 큰 금액을 지출한 고객으로, "
#"Monetary까지 함께 봐야 이런 '숨어있는 고가치 고객'을 놓치지 않을 수 있다."

#3
#"이탈위험군 795명 중 절반만이라도 재구매를 유도할 수 있다면(예: 타겟 할인 쿠폰, 재입고 알림 메일), "
#"매출에 상당한 영향을 줄 수 있다. 특히 이들 중에는 과거 Monetary가 높았지만 최근 Recency만 나빠진 고객도 섞여 있을 수 있어, "
#"'한때 VIP였던 이탈 고객'을 우선순위로 타겟팅하는 게 효율적일 것이다."

#===피드백===
#"주장 → 근거/예시 → (필요하면) 구체적 액션
#숫자나 사례를 근거로 구체적으로 말하기, 명확하게 쓰기