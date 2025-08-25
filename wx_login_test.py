import re
import time

from parsel import Selector
import requests
from loguru import logger
from qrcode.main import QRCode


class WXLogin:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:141.0) Gecko/20100101 Firefox/141.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Referer": "https://open.weixin.qq.com/",
        "Sec-GPC": "1",
        "Upgrade-Insecure-Requests": "1",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Priority": "u=0, i"
    }
    def __init__(self,
                 callback_url = "http://cas.swust.edu.cn/authserver/callback",
                 appid = "wx3e5a3c590b52de4d",
                 response_type = "code",
                 scope = "snsapi_login",
                 service = "https://soa.swust.edu.cn/sys/portal/page.jsp"
                 ):
        self.uuid = None
        self.session = requests.Session()
        self.callback_url = callback_url
        self.appid = appid
        self.response_type = response_type
        self.scope = scope
        self.service = service



    def wx_login(self):
        url = f"https://open.weixin.qq.com/connect/qrconnect?appid={self.appid}&redirect_uri={self.callback_url}&response_type={self.response_type}&scope={self.scope}#wechat_redirect"
        res = self.session.get(url,verify=False)
        qrcode = Selector(text=res.text)
        img_url = "https://open.weixin.qq.com" + qrcode.css(".js_qrcode_img::attr(src)").get()
        self.uuid = img_url.split('/')[-1]
        with open("qrcode.png", "wb") as f:
            f.write(self.session.get(img_url).content)
        logger.info("请使用微信扫码登录: ")
        qr = QRCode()
        qr.add_data(f"https://open.weixin.qq.com/connect/confirm?uuid={self.uuid}")
        qr.print_ascii()
        self.check_wx_login()

    def check_wx_login(self):
        while True:
            url = f"https://open.weixin.qq.com/connect/l/qrconnect?uuid={self.uuid}"
            res = self.session.get(url,verify=False)
            logger.debug(res.status_code)
            logger.debug(res.text)
            logger.debug("==============")
            wxcode = re.findall("wx_code='(.*)'", res.text)[0]
            if wxcode:
                logger.success(f"获取到wxcode: {wxcode}")
                call_back_url = f"{self.callback_url}?code={wxcode}&store="
                logger.info(f"跳转到{call_back_url}")
                call_res = self.session.get(call_back_url, headers=self.headers,verify=False)
                service_res = self.session.get(self.service, headers=self.headers,verify=False)
                logger.info(service_res.status_code)
                logger.info("=============")
                logger.success("登录成功")
                break
            time.sleep(1)

    def get_session(self):
        return self.session
