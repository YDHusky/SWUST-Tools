import json

from oa_auth import OAAuth
from parsel import Selector


oa = OAAuth(service="https://matrix.dean.swust.edu.cn/acadmicManager/index.cfm?event=studentPortal:DEFAULT_EVENT")
if oa.login("",""):
    session = oa.get_session()

    res = session.get("https://matrix.dean.swust.edu.cn/acadmicManager/index.cfm?event=chooseCourse:courseTable")
    document = Selector(res.text)
    class_table = document.css("#choosenCourseTable tbody")
    trs = class_table.css("tr")
    time = 0
    class_table = []

    for td in trs:
        time += 1
        trs = td.css("td")
        if len(trs) == 8:
            tr_count = 0
            for tr in trs:
                tr_count += 1
                if tr_count == 0:
                    continue
                lecture = tr.css(".lecture")
                if lecture:
                    class_name = lecture.css(".course::text").get().strip()
                    teacher = lecture.css(".teacher::text").get().strip()
                    week = lecture.css(".week::text").get().strip()
                    start_time = week.split("-")[0]
                    end_time = week.split("-")[1].split("(")[0]
                    place = lecture.css(".place::text").get().strip()
                    class_table.append({
                        "class_name": class_name,
                        "teacher": teacher,
                        "location": place,
                        "start_time": start_time,
                        "end_time": end_time,
                        "week_day": tr_count-1,
                        "time": time
                    })
        else:
            tr_count = 0
            for tr in trs:
                tr_count += 1
                if tr_count == 0 or tr_count == 1:
                    tr_count += 1
                    continue
                lecture = tr.css(".lecture")
                if lecture:
                    class_name = lecture.css(".course::text").get()
                    teacher = lecture.css(".teacher::text").get().strip()
                    week = lecture.css(".week::text").get().strip()
                    start_time = week.split("-")[0]
                    end_time = week.split("-")[1].split("(")[0]
                    place = lecture.css(".place::text").get().strip()
                    class_table.append({
                        "class_name": class_name,
                        "teacher": teacher,
                        "location": place,
                        "start_time": start_time,
                        "end_time": end_time,
                        "week_day": tr_count-2,
                        "time": time
                    })
    with open('table.json', 'w') as f:
        json.dump(class_table, f)
    print(class_table)
