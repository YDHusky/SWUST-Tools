import logging
import time

from oa_auth import OAAuth
from concurrent.futures import ThreadPoolExecutor
from parsel import Selector
from loguru import logger

from wx_login_test import WXLogin
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(filename)s - %(levelname)s - %(message)s')

class ClassSpider:
    def __init__(self, ct=1):
        self.class_type = ["programTask", "commonTask", "sportTask"]
        self.choose_params = {
            "sportTask": "SportTask",
            "commonTask": "CommonTask",
            "programTask": "PlanTask",

        }
        self.ct = ct
        # self.oa = OAAuth(
        #     service="https://matrix.dean.swust.edu.cn/acadmicManager/index.cfm?event=studentPortal:DEFAULT_EVENT")
        # self.oa.login(username, password)
        self.oa = WXLogin(service="https://matrix.dean.swust.edu.cn/acadmicManager/index.cfm?event=studentPortal:DEFAULT_EVENT")
        self.oa.wx_login()
        # /acadmicManager/index.cfm?event=chooseCourse:programTask&CT=2
        self.headers = {
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": "https://matrix.dean.swust.edu.cn",
            "priority": "u=1, i",
            "referer": f"https://matrix.dean.swust.edu.cn/acadmicManager/index.cfm?event=chooseCourse:sportTask&CT={ct}",
            "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest"
        }

    def get_class_main(self):
        executor = ThreadPoolExecutor(max_workers=4)
        for class_type in self.class_type:
            executor.submit(self.get_class_one_type, class_type)
        executor.shutdown(wait=True)

    def get_class_one_type(self, class_type):
        data_list = self.get_class_id(class_type)
        executor = ThreadPoolExecutor(max_workers=8)
        for item in data_list:
            executor.submit(self.get_class_one, class_type, item)
        executor.shutdown(wait=True)

    def get_class_one(self, class_type, class_data):
        class_list = self.get_class_info(class_type, class_data)
        for class_info in class_list:
            if "data" in class_info:
                class_info['data'].update({"class_type": class_type})
                if self.get_class_one_by_data(class_info['data'], class_data['name']):
                    return
            else:
                logger.warning("当前课程已满! ", class_data['name'])

    def get_class_one_by_data(self, data, name=""):
        url = "https://matrix.dean.swust.edu.cn/acadmicManager/index.cfm"
        params = {
            "event": f"chooseCourse:apiChoose{self.choose_params[data['class_type']]}"
        }
        res = self.oa.get_session().post(url, data=data, headers=self.headers, params=params,verify=False)
        if res.json()['success']:
            logger.success(f"成功选择: {name}")
            return True
        else:
            logger.error(f"选择失败: {name}")
            return False

    def get_class_id(self, class_type):
        url = f"https://matrix.dean.swust.edu.cn/acadmicManager/index.cfm?event=chooseCourse:{class_type}&CT={self.ct}"
        res = self.oa.get_session().get(url,verify=False)
        document = Selector(text=res.text)
        class_list = document.css(".courseShow")
        data_list = []
        for class_item in class_list:
            data = {
                "name": class_item.css(".name::text").get(),
                "cid": class_item.css(".trigger::attr(cid)").get(),
            }
            data_list.append(data)
        return data_list

    def get_class_info(self, class_type, data, index=None):
        url = "https://matrix.dean.swust.edu.cn/acadmicManager/index.cfm"
        params = {
            "event": f"chooseCourse:api{self.choose_params[class_type]}Table"
        }
        data = {
            "CID": data["cid"],
        }
        res = self.oa.get_session().post(url, data=data, headers=self.headers, params=params,verify=False)
        document = Selector(text=res.text)
        data = document.css(".editRows")
        t_header = document.css("thead td::text").getall()
        t_header.insert(0, "状态")
        data_list = []
        if index is not None:
            out = self.deal_class_info(data[index], t_header, class_type)
            return [out]
        for item in data:
            data_list.append(self.deal_class_info(item, t_header, class_type))
        return data_list

    def deal_class_info(self, item, t_header, class_type):
        js_code = item.css("a::attr(href)").get()
        item_data = {}
        if not js_code:
            item_data.update({t_header[0]: "已满"})
        else:
            item_data.update({t_header[0]: "空余"})
            js_code = js_code.replace(" ", "")
            choose_data = js_code.split("chooseCourse(")[1].strip(")';").split("','")
            # 将参数转换为字典
            data = {
                "CT": str(self.ct),  # 这个值是固定的，根据你的要求
                "TID": choose_data[2].strip("'"),
                "CID": choose_data[0].strip("'"),
                "CIDX": choose_data[1].strip("'"),
                "TSK": choose_data[4].strip("'"),
                "TT": choose_data[3].strip("'"),
                "ST": choose_data[5].strip("'"),
                "seed": int(time.time() * 1000)
            }
            if class_type == "programTask":
                data.update({"CP": 2})

            item_data.update({"data": data})
        tds = item.css("td::text").getall()

        for i in range(1, len(tds)):
            item_data.update({t_header[i]: tds[i].strip()})
        return item_data

    def get_class(self):
        for i in range(len(self.class_type)):
            print(f"[{i}] {self.class_type[i]}")
        class_type_id = int(input("请输入对应课程类型编号: "))
        _class_list: list = self.get_class_id(self.class_type[class_type_id])
        class_list = _class_list.copy()
        count = 0
        for c in range(len(_class_list)):
            if _class_list[c]["cid"] is None:
                class_list.pop(c - count)
                count += 1
                continue
            print(f"[{c - count}] {_class_list[c]['name']}")
        class_select = int(input("请输入对应课程编号: "))

        class_info_list = self.get_class_info(self.class_type[class_type_id], class_list[class_select])
        import pandas as pd
        df = pd.DataFrame(class_info_list)

        try:
            df = df.drop(['data'], axis=1)
        except:
            pass
        print(df)
        print(f"[{len(class_info_list)}] 小孩子才做选择，我全都要")
        index = int(input("请输入要抢的课程编号: "))
        a_count = 0
        while True:
            a_count += 1
            logger.info(f"第{a_count}次尝试...")
            try:
                if index < len(class_info_list):
                    class_info = self.get_class_info(self.class_type[class_type_id], class_list[class_select],
                                                     index=index)
                else:
                    class_info = self.get_class_info(self.class_type[class_type_id], class_list[class_select])
                for ci in class_info:
                    if "data" in ci:
                        ci["data"].update({"class_type": self.class_type[class_type_id]})
                        self.get_class_one_by_data(ci["data"])
                        break
            except:
                pass

    def main(self):
        time.sleep(0.5)
        options = ["一个不漏", "全部计划课程", "全部通识课程", "全部体育课程", "捡漏见缝插针"]
        for i in range(len(options)):
            print(f"[{i}] {options[i]}")
        index = int(input("请输入操作编号: "))
        count = 0
        if index == 0:
            while True:
                count += 1
                logger.info(
                    f"---------------------------------------------- 第{count}次 ----------------------------------------------")
                self.get_class_main()

        elif index == 1:
            while True:
                count += 1
                logger.info(
                    f"---------------------------------------------- 第{count}次 ----------------------------------------------")
                self.get_class_one_type("programTask")
        elif index == 2:
            while True:
                count += 1
                logger.info(
                    f"---------------------------------------------- 第{count}次 ----------------------------------------------")
                self.get_class_one_type("commonTask")
        elif index == 3:
            while True:
                count += 1
                logger.info(
                    f"---------------------------------------------- 第{count}次 ----------------------------------------------")
                self.get_class_one_type("sportTask")
        elif index == 4:
            self.get_class()


if __name__ == '__main__':
    test = ClassSpider(ct=2)
    test.main()
