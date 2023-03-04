"""
@author: xuxiangfeng
@date: 2023/3/4
@file_name: message_utils.py
"""
import requests
import json
from loguru import logger


def send_wechat_msg(content_text):
    """
    发送消息到企业微信群中
    """
    url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=8165d8d4-591f-4862-be01-3f4281d2da39"
    headers = {"Content-Type": "application/json;charset=utf-8"}

    msg = {
        "msgtype": "text",
        "text": {"content": content_text, "mentioned_list": []}
    }
    try:
        requests.post(url, data=json.dumps(msg), headers=headers)
    except Exception as e:
        logger.info(f"send wechat fail, error info: {e}")

