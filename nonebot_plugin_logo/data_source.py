import base64
import jinja2
import imageio
import pkgutil
import traceback
from io import BytesIO
from pathlib import Path
from jinja2 import Template
from typing import List, Union

from nonebot.log import logger
from nonebot_plugin_htmlrender import get_new_page, html_to_pic

env = jinja2.Environment(enable_async=True)


def get_tpl(name: str) -> Template:
    return env.from_string(pkgutil.get_data(__name__, f"templates/{name}").decode())


pb_tpl = get_tpl('pornhub.html')
yt_tpl = get_tpl('youtube.html')
cy_tpl = get_tpl('5000choyen.html')
dy_tpl = get_tpl('douyin.html')


async def create_pornhub_logo(left_text, right_text) -> bytes:
    html = await pb_tpl.render_async(left_text=left_text, right_text=right_text)
    return await html_to_pic(html, wait=0, viewport={"width": 100, "height": 100})


async def create_youtube_logo(left_text, right_text) -> bytes:
    html = await yt_tpl.render_async(left_text=left_text, right_text=right_text)
    return await html_to_pic(html, wait=0, viewport={"width": 100, "height": 100})


async def create_5000choyen_logo(top_text, bottom_text) -> str:
    html = await cy_tpl.render_async(top_text=top_text, bottom_text=bottom_text)

    async with get_new_page() as page:
        await page.set_content(html)
        a = await page.query_selector('a')
        img = await (await a.get_property('href')).json_value()
    return 'base64://' + str(img).replace('data:image/png;base64,', '')


async def create_douyin_logo(text) -> BytesIO:
    html = await dy_tpl.render_async(text=text, frame_num=10)

    async with get_new_page() as page:
        await page.set_content(html)
        imgs = await page.query_selector_all('a')
        imgs = [await (await img.get_property('href')).json_value() for img in imgs]

    imgs = [imageio.imread(base64.b64decode(
        str(img).replace('data:image/png;base64,', ''))) for img in imgs]

    output = BytesIO()
    imageio.mimsave(output, imgs, format='gif', duration=0.2)
    return output


commands = {
    'pornhub': {
        'aliases': {'ph ', 'phlogo'},
        'func': create_pornhub_logo,
        'arg_num': 2
    },
    'youtube': {
        'aliases': {'yt ', 'ytlogo'},
        'func': create_youtube_logo,
        'arg_num': 2
    },
    '5000choyen': {
        'aliases': {'5000兆', '5000choyen'},
        'func': create_5000choyen_logo,
        'arg_num': 2
    },
    'douyin': {
        'aliases': {'dylogo'},
        'func': create_douyin_logo,
        'arg_num': 1
    }
}


async def create_logo(texts: List[str], style: str) -> Union[str, bytes, BytesIO, Path]:
    try:
        func = commands[style]['func']
        return await func(*texts)
    except:
        logger.warning(traceback.format_exc(limit=1))
        return None
