import time
import logging

from django.template.loader import render_to_string

from app import constants
from app.wechat.qiubai import get_joke
from app.wechat.replay_rules import rules
from app.wechat.invitecode import get_invite_code

logger = logging.getLogger('default')


def main_handler(xml):
    # 找到传来的消息事件：
    # 如果普通用户发来短信，则event字段不会被捕捉
    event = xml.find('Event')
    event = event.text if event is not None else None
    # 找到此次传送的消息信息的类型和内容
    msg_type = xml.find('MsgType')
    msg_content = xml.find('Content')
    msg_type = msg_type.text if msg_type is not None else None
    msg_content = msg_content.text if msg_content is not None else None

    logger.info("msg_type: {} event: {} content:{}".format(
        msg_type, event, msg_content))

    # 判断是否是新关注的用户
    if event == 'subscribe':
        text = constants.SUBSCRIBE_TEXT
        return parse_text(xml, text)

    if msg_type == 'image':
        parse_image(xml)
    elif msg_type == 'text':
        # 当收到的信息在处理规则之中时
        if msg_content == '邀请码':
            text = get_invite_code()
            return parse_text(xml, text)
        # 针对段子特殊处理
        elif msg_content == '段子' or msg_content == '来个段子':
            text = get_joke()
            return parse_text(xml, text)
        elif msg_content in rules.keys():
            text = rules[msg_content]
            return parse_text(xml, text)
        # 当不属于规则是，返回一个功能引导菜单
        else:
            return parse_text(xml, text=constants.NAV_BAR)
    else:
        return 'success'


def parse_text(xml, text):
    '''
    处理微信发来的文本数据
    返回处理过的xml
    '''
    # 反转发件人和收件人的消息
    fromUser = xml.find('ToUserName').text
    toUser = xml.find('FromUserName').text
    # event事件是没有有msg id 的
    message_id = xml.find('MsgId')
    message_id = message_id.text if message_id is not None else ''
    # 我们来构造需要返回的时间戳
    nowtime = str(int(time.time()))
    context = {
        'FromUserName': fromUser,
        'ToUserName': toUser,
        'Content': text,
        'time': nowtime,
        'id': message_id,
    }
    # 我们来构造需要返回的xml
    respose_xml = render_to_string('wechat/wx_text.xml', context=context)

    return respose_xml


def parse_image(xml):
    '''
    处理微信发来的图片数据
    '''
    # 反转发件人和收件人的消息
    fromUser = xml.find('ToUserName').text
    toUser = xml.find('FromUserName').text
    nowtime = str(int(time.time()))
    media_id = xml.find('MediaId').text
    context = {
        'FromUserName': fromUser,
        'ToUserName': toUser,
        'time': nowtime,
        'media_id': media_id
    }
    # 我们来构造需要返回的xml
    respose_xml = render_to_string('wechat/wx_image.xml', context=context)
    return respose_xml