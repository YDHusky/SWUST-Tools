import re
import time

from parsel import Selector
import requests

url = "https://open.weixin.qq.com/connect/qrconnect?appid=wx3e5a3c590b52de4d&redirect_uri=http://cas.swust.edu.cn/authserver/callback&response_type=code&scope=snsapi_login#wechat_redirect"

res = requests.get(url)

qrcode = Selector(text=res.text)

img_url = "https://open.weixin.qq.com" + qrcode.css(".js_qrcode_img::attr(src)").get()
uuid = img_url.split('/')[-1]
print(uuid)
print(img_url)


while True:
    url = "https://open.weixin.qq.com" + f"/connect/l/qrconnect?uuid={uuid}"
    res = requests.get(url)
    print(res.text)
    print(res.status_code)
    print("==============")
    wxcode = re.findall("wx_code='(.*)'", res.text)[0]
    if wxcode:
        print(wxcode)
        break
    time.sleep(1)