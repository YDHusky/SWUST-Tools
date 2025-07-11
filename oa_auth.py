import time

import requests
from loguru import logger
import ddddocr
from parsel import Selector
from selenium import webdriver


class OAAuth:
    def __init__(self, service="https://soa.swust.edu.cn/", max_post=3):
        self.session = requests.Session()
        self.session.verify = False
        self.ocr = ddddocr.DdddOcr(show_ad=False)
        self.service = service
        self.max_post = max_post

    def get_key(self):
        base_url = "https://cas.swust.edu.cn/authserver/getKey"
        res = self.session.get(base_url)
        logger.debug("获取到公钥参数:{}", res.text)
        return res.json()['exponent'], res.json()['modulus']

    def get_captcha(self):
        base_url = "https://cas.swust.edu.cn/authserver/captcha"
        res = self.session.get(base_url)
        captcha = self.ocr.classification(res.content)
        logger.debug("获取到验证码:{}", captcha)
        return captcha

    @staticmethod
    def encrypt_password(modules, password, public_exponent="10001"):
        public_modulus = int(modules, 16)
        public_exponent = int(public_exponent, 16)
        password = "".join(reversed(password))
        plaintext = int(password[::-1].encode("utf-8").hex(), 16)
        encrypted_password = pow(plaintext, public_exponent, public_modulus)
        return "%x" % encrypted_password

    def get_login(self):
        base_url = "https://cas.swust.edu.cn/authserver/login"
        params = {
            "service": self.service,
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Sec-GPC": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Priority": "u=0, i"
        }
        res = self.session.get(base_url, params=params, headers=headers)
        html = Selector(res.text)
        execution = html.css("input[name='execution']::attr(value)").get()
        _eventId = html.css("input[name='_eventId']::attr(value)").get()
        logger.debug("获取到execution:{}", execution)
        logger.debug("获取到_eventId:{}", _eventId)
        return {
            "execution": execution,
            "_eventId": _eventId,
            "geolocation": "",
            "lm": "usernameLogin"
        }

    def post_login(self, username, password):
        base_url = "https://cas.swust.edu.cn/authserver/login"
        params = {
            "service": self.service,
        }
        exponent, modulus = self.get_key()
        payload = {
            "username": username,
            "password": self.encrypt_password(modulus, password, exponent),
            "captcha": self.get_captcha(),
        }
        payload.update(self.get_login())
        logger.debug("post payload: {}", payload)

        res = self.session.post(base_url, params=params, data=payload)
        # logger.debug("post res: {}", res.text)
        if res.status_code == 200:

            return True
        else:
            return False

    def login(self, username, password):
        post_count = 0
        is_success = False
        while post_count < self.max_post:
            post_count += 1
            post_login = self.post_login(username, password)

            if post_login:
                logger.success("协议登录成功！")
                is_success = True
                break
            else:
                logger.error("第{}次尝试登录失败，尝试重新登录中...", post_count)
        if not is_success:
            logger.error("登录失败，尝试次数达到最大，请检查账号密码是否正确!")
            return False
        else:
            return True

    def get_session(self):
        return self.session

    def get_cookies(self):
        cookies = self.session.cookies.get_dict()
        selenium_cookies = []
        for k, v in cookies.items():
            selenium_cookies.append({
                "name": k,
                "value": v,
            })
        return selenium_cookies

    def get_firefox_driver(self):
        driver = webdriver.Firefox()
        driver.get("https://cas.swust.edu.cn/authserver/login")
        for i in self.get_cookies():
            driver.add_cookie(i)
        driver.refresh()
        return driver


