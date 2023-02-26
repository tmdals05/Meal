 # -*- coding: utf-8 -*-
import requests
from flask import Flask, jsonify, request, send_file
import sys
from datetime import datetime, timedelta
import datetime
import json
import re
import schedule
import os
import urllib.request

application = Flask(__name__)

Days = ['(월)', '(화)', '(수)', '(목)', '(금)', '(토)', '(일)']

time_difference = 9 #이 코드를 켜놓는 서버가 미국에 있어 시차 적용
Today = datetime.datetime.now() + timedelta(hours=time_difference)

images_folder = "Meal/TimeTable/"
# images_folder = "C:/Users/danie/OneDrive/문서/Python Scripts/TimeTable/"

def is_vacation(DATE): #요청된 요일이 방학기간인지 확인
    if datetime.datetime.strptime("20220720", "%Y%m%d") < DATE < datetime.datetime.strptime("20220822", "%Y%m%d"):
        return DATE.strftime("%Y-%m-%d") + "\n해당하는 요일은 여름방학 기간입니다"
    elif datetime.datetime.strptime("20221230", "%Y%m%d") < DATE < datetime.datetime.strptime("20230201", "%Y%m%d"):
        return DATE.strftime("%Y-%m-%d") + "\n해당하는 요일은 겨울방학 기간입니다"
    elif datetime.datetime.strptime("20230208", "%Y%m%d") < DATE < datetime.datetime.strptime("20230301", "%Y%m%d"):
        return DATE.strftime("%Y-%m-%d") + "\n해당하는 요일은 봄방학 기간입니다"
    else:
        return 0

def is_weekend(DATE): #요청된 요일이 주말인지 확인
    if DATE.weekday() == 5:
        return DATE.strftime("%Y-%m-%d") + "\n해당하는 요일은 토요일입니다"
    elif DATE.weekday() == 6:
        return DATE.strftime("%Y-%m-%d") + "\n해당하는 요일은 일요일입니다"
    else:
        return 0

def load_data(SCHOOL_CODE, MEAL, DATE): #나이스 교육정보 개방 포털애서 급식 정보를 불러옴
    API_KEY = '02d070cf271a46259611f05b0b03e9e6'
    CLEAR_DATE = DATE.strftime('%Y%m%d')
    url = 'https://open.neis.go.kr/hub/mealServiceDietInfo'
    queryParams = '?' + \
                'KEY=' + API_KEY + \
                '&Type='+ 'json' + \
                '&pIndex='+ '1' + \
                '&pSize='+ '10' + \
                '&ATPT_OFCDC_SC_CODE='+ 'N10' + \
                '&SD_SCHUL_CODE='+ SCHOOL_CODE + \
                '&MMEAL_SC_CODE='+ MEAL + \
                '&MLSV_YMD='+ str(CLEAR_DATE)

    response = requests.get(url + queryParams)
    contents = response.text
    json_ob = json.loads(contents)
    #print(json_ob)
    return json_ob

def get_meal_info(json_ob): #불러온 정보에서 급식 정보를 가공함
    try:
        body = json_ob['mealServiceDietInfo'][1]['row']

        for i in range(len(body)):
            temp = body[i]['DDISH_NM']
        
        temp = temp.replace('<br/>', '\n')
        temp = re.sub(r'\([^)]*\)', '', temp)
        return temp
    except:
        temp = "서버에서 불러올 데이터가 없습니다\nMENU_INFO_ERROR"
        return temp

def get_cal_info(json_ob): #불러온 정보에서 열량 정보를 가공함
    try:
        body = json_ob['mealServiceDietInfo'][1]['row']

        for i in range(len(body)):
            cal_info = body[i]['CAL_INFO']
        
        return cal_info
    except:
        return 0

def meal_function(SCHOOL_CODE, MEAL, DATE): #모든 정보를 보기 좋게 합침
    if is_vacation(DATE) != 0:
        return is_vacation(DATE)

    if is_weekend(DATE):
        return is_weekend(DATE)

    json_ob = load_data(SCHOOL_CODE, MEAL, DATE)

    if get_meal_info(json_ob) == 0:
        return "서버에서 불러올 데이터가 없습니다\nMENU_INFO_ERROR"
    else:
        meal_info = get_meal_info(json_ob)
    #print(meal_info)
    if get_cal_info(json_ob) == 0:
        return "서버에서 불러올 데이터가 없습니다\nCAL_INFO_ERROR"
    else:
        cal_info = get_cal_info(json_ob)
    #print(cal_info)

    if int(MEAL) == 2:
        MEAL_MENU = ' 중식 메뉴'
    elif int(MEAL) == 3:
        MEAL_MENU = ' 석식 메뉴'

    meal_date = DATE.strftime("%Y-%m-%d")
    day_of_week = datetime.date(int(DATE.strftime('%Y')), int(DATE.strftime('%m')), int(DATE.strftime('%d'))).weekday()
    try:
        meal_final = (meal_date + Days[day_of_week % 7] + MEAL_MENU + "\n\n" + meal_info + "\n\n(" + cal_info + ")")
    except:
        meal_final = "서버에서 불러올 데이터가 없습니다\nFINAL_ERROR"
        return meal_final

    meal_real_final = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": (meal_final)
                    }
                }
            ]
        }
    }
    #print(meal_real_final)
    return meal_real_final
    
def last_check(text): #마지막으로 보낼 수 있는 문자열인지 확인함
    if 'version' not in text:
        return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": (text)
                    }
                }
            ]
        }
    }
    else:
        return text

@application.route("/lunch/today", methods=["POST"])
def lunch_today_function(): #오늘 점심
    #print(request.get_json())
    response = meal_function('8140387', '2', Today)
    return jsonify(last_check(response))

@application.route("/dinner/today", methods=["POST"])
def dinner_today_function(): #오늘 석식
    response = meal_function('8140387', '3', Today)
    return jsonify(last_check(response))

Tomorrow = datetime.datetime.today() + timedelta(hours=time_difference) + timedelta(days = 1)

@application.route("/lunch/tomorrow", methods=["POST"])
def lunch_tomorrow_function(): #내일 점심
    response = meal_function('8140387', '2', Tomorrow)
    return jsonify(last_check(response))

@application.route("/dinner/tomorrow", methods=["POST"])
def dinner_tomorrow_function(): #내일 석식
    response = meal_function('8140387', '3', Tomorrow)
    return jsonify(last_check(response))

@application.route("/meal/choose", methods=["POST"])
def meal_choose(): #원하는 날짜 선택
    body = request.get_json()
    json_ob = body['action']['detailParams']['date']['origin']
    json_ob = json_ob.replace('-', ' ')
    datetime_string = json_ob
    datetime_format = "%Y %m %d"
    DATE = datetime.datetime.strptime(datetime_string, datetime_format)
    body = request.get_json()
    json_ob = body['action']['detailParams']['type']['origin']
    if json_ob == "중식":
        meal_type = 2
    if json_ob == "석식":
        meal_type = 3
    response = meal_function('8140387', str(meal_type), DATE)
    return jsonify(last_check(response))
    
          
@application.route("/lunch/cheonan", methods=["POST"])
def cheonan_lunch_today_function(): #천안고 오늘 점심
    DATE = datetime.datetime.today() + datetime.timedelta(hours=time_difference)
    response = meal_function('8140104', '2', DATE)
    return jsonify(last_check(response))

@application.route("/getimetable", methods=["POST"])
def get_timetable():
    body = request.get_json()
    secureUrls = body['action']['params']['TimeTable_Image']
    start = secureUrls.find("(")
    end = secureUrls.find(")")
    if start != -1 and end != -1:
        extracted_url = secureUrls[start+1:end]
    UserID = body['userRequest']['user']['id']
    file_path = images_folder + UserID + ".png"

    if os.path.exists(file_path):
        os.remove(file_path)
        urllib.request.urlretrieve(extracted_url, file_path)
        return last_check("이미 이미지가 있어 이미지를 덮어씌웠습니다.")
    else:
        urllib.request.urlretrieve(extracted_url, file_path)
        return last_check("이미지 업로드를 완료하였습니다.")

@application.route("/giveTimetable", methods=["POST"])
def give_timetable():
    body = request.get_json()
    UserID = body['userRequest']['user']['id']
    #print(UserID)
    file_path = images_folder + UserID + ".png"
    if os.path.isfile(file_path):
        location = "http://bdhs.kro.kr:80/image/" + UserID + ".png"
        return {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleImage": {
                            "imageUrl": (location)
                        }
                    }
                ]
            }
        }
    else:
        return last_check("이미지가 업로드 되어있지 않습니다.\n\"시간표 설정\"을 입력하여 시간표를 업로드 해주세요")
    
@application.route("/delTimetable", methods=["POST"])
def del_timetable():
    body = request.get_json()
    UserID = body['userRequest']['user']['id']
    file_path = images_folder + UserID + ".png"
    if os.path.isfile(file_path):
        os.remove(file_path)
        return last_check("시간표를 삭제하였습니다.")
    else:
        return last_check("시간표가 업로드 되어있지 않습니다.")

@application.route("/")
def index():
    html = ""
    for filename in os.listdir("/Meal/TimeTable"):
        if filename.endswith(".png"):
            html += f"<p><img src='/image/{filename}'></p>"
    return html

@application.route("/image/<path:filename>")
def get_image(filename):
    filepath = os.path.join("/Meal/TimeTable/", filename)
    if not os.path.isfile(filepath) or os.path.isabs(filename):
        return "", 404
    return send_file(filepath, mimetype="image/png")

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=int(sys.argv[1]), debug=True)

schedule.every().day.at("00:00").do(meal_function)
