import shlex
import traceback
from nonebot import on_command
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.typing import T_Handler
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import MessageSegment, Message

from .data_source import commands, Command

__plugin_meta__ = PluginMetadata(
    name="logo生成",
    description="pornhub等风格logo生成",
    usage=(
        "pornhub：ph {text1} {text2}"
        "youtube：yt {text1} {text2}"
        "5000兆円欲しい!：5000兆 {text1} {text2}"
        "抖音：douyin {text}"
        "谷歌：google {text}"
    ),
    extra={
        "unique_name": "logo",
        "example": "ph Porn Hub\nyt You Tube\n5000兆 我去 初音未来",
        "author": "meetwq <meetwq@gmail.com>",
        "version": "0.2.2",
    },
)


def create_matchers():
    def create_handler(command: Command) -> T_Handler:
        async def handler(matcher: Matcher, msg: Message = CommandArg()):
            text = msg.extract_plain_text().strip()
            if not text:
                await matcher.finish()

            arg_num = command.arg_num
            if arg_num == 1:
                texts = [text]
            else:
                try:
                    texts = shlex.split(text)
                except:
                    texts = text.split()
            if len(texts) != arg_num:
                await matcher.finish(f"参数数量不符，需要发送{arg_num}段文字")

            try:
                image = await command.func(texts)
            except:
                logger.warning(traceback.format_exc())
                await matcher.finish("出错了，请稍后再试")

            await matcher.finish(MessageSegment.image(image))

        return handler

    for command in commands:
        on_command(
            command.keywords[0], aliases=set(command.keywords), priority=13, block=True
        ).append_handler(create_handler(command))


create_matchers()
