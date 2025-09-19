
'''
관광타입 contentTypeId
(12:관광지, 14:문화시설, 15:축제공연행사, 25:여행코스, 28:레포츠, 32:숙박, 38:쇼핑, 39:음식점)
'''

###########################################
## 야경 명소, 야시장, 밤까지 운영하는 곳 추출 ##
###########################################

''' 
how finding?
- title 컬럼에서 "야경", "야시장", "전망대" 같은 단어가 들어간 것만 골라보기
- 또는 contenttypeid 기준으로 음식점(39) 빼고 관광지(12), 문화시설(14)만 남기기
'''


# 야경 키워드로 필터링
import pandas as pd

df = pd.read_csv('../daegu_tourlist_full.csv') # 대구 전체 리스트

# 방법1) 간단한 키워드 필터링
# - 아래 코드의 문제점: '서문시장', '83타워'와 같이 키워드가 명시안된 관광지는 제외됨 → 7곳만 추출됨
# keywords = ['야경', '야시장', '전망대', '야간']                          # na=False: 값 비어있는 경우 False로 간주
# df_night = df[df['title'].str.contains('|'.join(keywords), na=False)] # 정규표현식(또는) → 야경|야시장|전망대

# print(f"🔦 야간 관광지 추정 결과: {len(df_night)}개")
# df_night.to_csv('night_tourlist.csv', index=False, encoding='utf-8-sig')


# 방법2) 🔥수작업으로 명소 선정🔥
# 관광지/문화시설만 남기기
df_filtered = df[df['contenttypeid'].isin([12, 14, 15])]

# 키워드 기반 필터
keywords = ['야경', '야시장', '전망대', '빛', '야간', '야외']
keyword_mask = df_filtered['title'].str.contains('|'.join(keywords), na=False)

# 수작업 지정 야간 명소 리스트
manual_night_places = ['83타워', '서문시장', '두류공원', '수창청춘맨숀', '김광석', '동성로']

# 수작업 포함 필터
manual_mask = df_filtered['title'].apply(lambda x: any(name in x for name in manual_night_places))

# 두 필터 결합
df_night = df_filtered[keyword_mask | manual_mask]

# df_night.to_csv('night_tourlist.csv', index=False, encoding='utf-8-sig')
print(f"🔦 야간 관광지 최종 필터링 결과: {len(df_night)}개") #  → 해당 데이터를 지도에 표시하면 야간 관광지도가 됨

####################
## 낮 관광지 필터링 ## 
####################

import pandas as pd

# 파일 불러오기
df_night = pd.read_csv("./night_tourlist.csv")

# title 기준으로 야간 관광지 제외(낮 관광지 후보만 남김)
df_day = df[~df['title'].isin(df_night['title'])].drop_duplicates().reset_index(drop=True)

# 낮 관광지 후보에서 contenttypeid가 볼거리에 해당하는 것만 남기기
day_type = [12, 14] # 관광지 / 문화시설
df_day_filtered = df_day[df_day['contenttypeid'].isin(day_type)].reset_index(drop=True)

# 주요 컬럼만 남김
df_day_result = df_day_filtered[['title', 'addr', 'mapx', 'mapy', 'contenttypeid']]

# 저장
# df_day_result.to_excel(day_excel_path, index=False, encoding='utf-8')
# df_day_result.to_csv('day_tourlist.csv', index=False, encoding='utf-8-sig')


print(f"🔦 주간 관광지 최종 필터링 결과: {len(df_day_result)}개")


############################
## 음식점 / 쇼핑 / 숙박 저장 ##
############################

# 음식점 (contenttypeid: 39)
df_food = df[df['contenttypeid'] == 39][['title', 'addr', 'mapx', 'mapy']]
df_food = df_food.drop_duplicates().reset_index(drop=True) # 중복된 행 제거 후 인덱스 0부터 

# 쇼핑 (contenttypeid: 38)
df_shopping = df[df['contenttypeid'] == 38][['title', 'addr', 'mapx', 'mapy']]
df_shopping = df_shopping.drop_duplicates().reset_index(drop=True)

# 숙박 (contenttypeid: 32)
df_stay = df[df['contenttypeid'] == 32][['title', 'addr', 'mapx', 'mapy']]
df_stay = df_stay.drop_duplicates().reset_index(drop=True)


df_food.to_csv('food_list.csv', index=False, encoding='utf-8-sig')
df_shopping.to_csv('shopping_list.csv', index=False, encoding='utf-8-sig')
df_stay.to_csv('stay_list.csv', index=False, encoding='utf-8-sig')

print(f"🔦 음식점 최종 필터링 결과: {len(df_food)}개")
print(f"🔦 쇼  핑 최종 필터링 결과: {len(df_shopping)}개")
print(f"🔦 숙  박 최종 필터링 결과: {len(df_stay)}개")




