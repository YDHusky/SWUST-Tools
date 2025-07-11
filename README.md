# SWUST工具集

## 文件说明

- oa_auth.py 核心登录(现已不适用，需要修改)
- class_spider.py 教务抢课脚本
- jkxb.py 事物辅助系统自动签到
- lab.py 新生实验室自动答题
- classTable.py 课表解析
- wx_login_test.py 一站式微信登录模拟实现

其余功能请自行研究

## 使用教程

```bash
pip install requirements.txt
```

> 注意，由于学校采用零信任，oaauth部分需要修改(
> 这里提出修改思路，可以使用selenium进行操作，这里推荐[husky-spider-utils](https://github.com/YDHusky/husky-spider-utils), [相关文档](https://spider.yudream.online/husky-spider-utils.html) )


## 抢课脚本已实现功能

- [x] 第一次针对性(计划课程，通选课，体育课)全选
- [x] 后续轮询针对性高并发捡漏

## 注意事项

本项目仅供参考学习，禁止用于商业
