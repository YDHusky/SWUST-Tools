import json
import requests
from loguru import logger

class JKXB:
    def __init__(self, username, password):
        self.session = requests.Session()
        self.username = username
        self.password = password
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
        }
        self.login(username,password)

    def login(self,username,password):
        url = "https://jkxb.swust.edu.cn/user/login"
        data = {
            "ID": username,
            "password": password,
            "loginByScanCode": None
        }
        data = json.dumps(data, separators=(',', ':'))
        response = self.session.post(url, headers=self.headers, data=data)
        print(response.text)
        if "成功" in response.text:
            logger.success("登录成功！用户ID:{}",response.json()['info']['ID'])
        else:
            logger.error("登录失败！")

    def get_single_sign_info(self,task_id,introduction):
        url = "https://jkxb.swust.edu.cn/task/get_single_sign_info"
        data = {
            "task_id": task_id,
            "ID": self.username,
        }
        res = self.session.post(url, data=data)
        logger.success("获取今日签到任务成功！data: {}",res.text)
        data = res.json()['data']
        data['introduction'] = introduction
        return data

    def sign_edit(self,sign_map_info="四川省绵阳市涪城区青义镇青龙大道中段107号西南科技大学青义校区"):
        introduction="{\"签到方式\":\"定位签到\",\"签到内容\":{\"签到状态\":\"签到成功\",\"使用位置信息编号\":[\"5bca4e88e26bcdbc384\",\"f72a2ffa6b4b038d4c9\",\"ee28e12a5e0a8bc817b\",\"9955c159178b709741b\"],\"使用范围信息\":\"[[104.698088,31.538095],[104.698116,31.536891],[104.699554,31.536843],[104.699639,31.53745],[104.69956,31.538068]],[[104.697229,31.538091],[104.697225,31.536808],[104.698706,31.536889],[104.698714,31.538104]],[[104.691899,31.538442],[104.691451,31.537912],[104.691344,31.537348],[104.692351,31.53719],[104.692501,31.537583],[104.692716,31.538026]],[[104.693312,31.538576],[104.693325,31.538334],[104.693662,31.538325],[104.693957,31.53799],[104.694247,31.538142],[104.693854,31.538617],[104.693681,31.538608]]\",\"签到坐标\":[104.698727,31.537019],\"签到位置名称\":\""+sign_map_info+"\"}}"
        url = "https://jkxb.swust.edu.cn/task/sign_edit"
        data = self.get_single_sign_info(self.get_task_id(),introduction)
        data = [data]
        res = self.session.post(url, headers=self.headers,data=json.dumps(data))
        if "成功" in res.text:
            """
            @todo 签到成功
            """
            logger.success("签到成功！{}",res.text)

    def get_task_id(self):
        url = "https://jkxb.swust.edu.cn/task/get_my_task_info_list"
        data = {}
        res = self.session.post(url, data=data)
        logger.success("获取签到任务成功！{}",res.text)
        return res.json()['data'][0]['task_id']

if __name__ == '__main__':
    jkxb = JKXB("","")
    jkxb.sign_edit()