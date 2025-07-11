import json
import re
import time

from loguru import logger
from selenium.webdriver.common.by import By

from oa_auth import OAAuth
from parsel import Selector


# paper_url = "https://aqks.swust.edu.cn/LabSafetyExamSchoolSSO/StartLabSafetyExamPlus.aspx?PaperID={}".format(paper_id)

class LabPaper:
    def __init__(self, username, password):
        self.oa = OAAuth(service="http://aqks.swust.edu.cn/LabSafetyExamSchoolSSO/Sindex.aspx")
        self.oa.login(username, password)
        self.session = self.oa.session
        self.driver = self.oa.get_firefox_driver()

    def get_paper_id(self):
        url = "https://aqks.swust.edu.cn/LabSafetyExamSchoolSSO/SchoolLevel/SchoolLevelExamList.aspx"
        res = self.session.get(url)
        selector = Selector(text=res.text)
        script = selector.css("script::text").getall()

        pattern = r"var f2_state=(.*?);var f2_columns"
        matches = re.findall(pattern, script[0], re.DOTALL)
        f2_state = json.loads(matches[0])
        paper_id = f2_state.get("F_Rows")[0].get("f0")[1]
        logger.success("获取到试卷id: {}", paper_id)
        return paper_id

    def to_paper(self):
        paper_url = "https://aqks.swust.edu.cn/LabSafetyExamSchoolSSO/StartLabSafetyExamPlus.aspx?PaperID={}".format(
            self.get_paper_id())
        self.driver.get(
            "https://aqks.swust.edu.cn/LabSafetyExamSchoolSSO/Sindex.aspx#/LabSafetyExamSchoolSSO/SchoolLevel/SchoolLevelExamList.aspx")
        self.driver.get(paper_url)

    def get_ans(self):
        self.driver.find_element(by=By.CSS_SELECTOR, value="#SubmitButton").click()
        selector = Selector(self.driver.page_source)
        cards = selector.css(".mb-3")
        import sqlite3
        conn = sqlite3.connect('LabSafetyExamSchoolSSO.db')
        cur = conn.cursor()

        for card in cards:
            question = ""
            if "（单选 1.5分）" in card.css(".card-header::text").get():
                question = card.css(".card-header::text").get().split("（单选 1.5分）")[-1].strip()
            elif "（多选 3分）" in card.css(".card-header::text").get():
                question = card.css(".card-header::text").get().split("（多选 3分）")[-1].strip()
                question += "dx"
            elif "（判断 2分）" in card.css(".card-header::text").get():
                question = card.css(".card-header::text").get().split("（判断 2分）")[-1].strip()
                question += "pd"
            form_groups = card.css(".form-group::text")
            answers = []
            for i in form_groups:
                answers.append(i.get().split(".")[-1].strip())
            answer = card.css(".card-footer::text").get().split("：")[-1].strip()
            ans = []
            if "A" in answer:
                ans.append(answers[0])
            if "B" in answer:
                ans.append(answers[1])
            if "C" in answer:
                ans.append(answers[2])
            if "D" in answer:
                ans.append(answers[3])
            if "E" in answer:
                ans.append(answers[4])
            if "F" in answer:
                ans.append(answers[5])
            if "对" in answer:
                ans.append("对")
            if "错" in answer:
                ans.append("错")
            arly_answers = self.query_question(self, question)
            if len(arly_answers) == 0:
                ans_text = "%fg%".join(ans)
                sql = "insert into lab(q,a) values (?,?)"
                cur.execute(sql, (question, ans_text))
            else:
                for i in ans:
                    if i not in arly_answers:
                        arly_answers.append(i)
                ans_text = "%fg%".join(arly_answers)
                sql = "update lab set a=? where q=?"
                cur.execute(sql, (ans_text, question))
            conn.commit()
        cur.close()
        conn.close()
        total = float(selector.css("#countdownTimer::text").get().replace("分", "").strip())
        if total >= 90:
            logger.success("通过！分数:{}", total)
        else:
            logger.error("考试失败！请重试,分数:{}", total)
        return total

    @staticmethod
    def query_question(self, question):
        import sqlite3
        conn = sqlite3.connect('LabSafetyExamSchoolSSO.db')
        cur = conn.cursor()
        sql = "select a from lab where q = ?"
        cur.execute(sql, (question,))
        data = cur.fetchone()
        if data:
            return data[0].split("%fg%")
        else:
            return []

    def xz(self):
        selector = Selector(self.driver.page_source)
        cards = selector.css(".mb-3")
        question_num = 1
        for card in cards:
            question = ""
            if "（单选 1.5分）" in card.css(".card-header::text").get():
                question = card.css(".card-header::text").get().split("（单选 1.5分）")[-1].strip()
            elif "（多选 3分）" in card.css(".card-header::text").get():
                question = card.css(".card-header::text").get().split("（多选 3分）")[-1].strip()
                question += "dx"
            elif "（判断 2分）" in card.css(".card-header::text").get():
                question = card.css(".card-header::text").get().split("（判断 2分）")[-1].strip()
                question += "pd"
            form_groups = card.css("label::text")
            answers = []
            for i in form_groups:
                answers.append(i.get().split(".")[-1].strip())
            ans = self.query_question(self, question)
            if len(ans) == 0:
                pass
            else:
                for i in ans:

                    for j in range(0, len(answers)):
                        if i in answers[j]:
                            abc = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
                            try:
                                self.driver.find_element(by=By.CSS_SELECTOR,
                                                         value=f"input[name='Question{question_num}'][value='{abc[j]}']").click()
                            except Exception as e:
                                print(e)
                        if i == "对" and answers[j] == "正确" or i == "错" and answers[j] == "错误":
                            dc = ['True', 'False']
                            try:
                                self.driver.find_element(by=By.CSS_SELECTOR,
                                                         value=f"input[name='Question{question_num}'][value='{dc[j]}']").click()
                            except Exception as e:
                                print(e)
            question_num += 1



info = input("请按照\"学号 密码\"输入:")
username = info.split(" ")[0]
password = info.split(" ")[1]
print(username)
print(password)
lab_paper = LabPaper(username, password)

total = 0
while total < 90:
    lab_paper.to_paper()
    lab_paper.xz()
    total = lab_paper.get_ans()
    time.sleep(1)
