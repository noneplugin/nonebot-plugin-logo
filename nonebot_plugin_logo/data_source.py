import base64
import jinja2
import imageio
from io import BytesIO
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Union, Protocol

from nonebot import require

require("nonebot_plugin_htmlrender")
from nonebot_plugin_htmlrender import get_new_page, html_to_pic


dir_path = Path(__file__).parent
template_path = dir_path / "templates"
path_url = f"file://{template_path.absolute()}"
env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_path), enable_async=True
)


async def to_image(html: str) -> bytes:
    return await html_to_pic(
        html, viewport={"width": 100, "height": 100}, template_path=path_url
    )


async def make_pornhub(texts: List[str]) -> bytes:
    template = env.get_template("pornhub.html")
    html = await template.render_async(left_text=texts[0], right_text=texts[1])
    return await to_image(html)


async def make_youtube(texts: List[str]) -> bytes:
    template = env.get_template("youtube.html")
    html = await template.render_async(left_text=texts[0], right_text=texts[1])
    return await to_image(html)


async def make_5000choyen(texts: List[str]) -> str:
    template = env.get_template("5000choyen.html")
    html = await template.render_async(top_text=texts[0], bottom_text=texts[1])

    async with get_new_page() as page:
        await page.goto(path_url)
        await page.set_content(html)
        await page.wait_for_selector("a")
        a = await page.query_selector("a")
        assert a
        img = await (await a.get_property("href")).json_value()
    return "base64://" + str(img).replace("data:image/png;base64,", "")


async def make_douyin(texts: List[str]) -> BytesIO:
    template = env.get_template("douyin.html")
    html = await template.render_async(text=texts[0], frame_num=10)

    async with get_new_page() as page:
        await page.goto(path_url)
        await page.set_content(html)
        imgs = await page.query_selector_all("a")
        imgs = [await (await img.get_property("href")).json_value() for img in imgs]

    imgs = [
        imageio.imread(base64.b64decode(str(img).replace("data:image/png;base64,", "")))
        for img in imgs
    ]

    output = BytesIO()
    imageio.mimsave(output, imgs, format="gif", duration=0.2)
    return output


async def make_google(texts: List[str]) -> bytes:
    template = env.get_template("google.html")
    html = await template.render_async(text=texts[0])
    return await to_image(html)


class Func(Protocol):
    async def __call__(self, texts: List[str]) -> Union[str, bytes, BytesIO, Path]:
        ...


@dataclass
class Command:
    keywords: Tuple[str, ...]
    func: Func
    arg_num: int = 1


commands = [
    Command(("pornhub", "ph ", "phlogo"), make_pornhub, 2),
    Command(("youtube", "yt ", "ytlogo"), make_youtube, 2),
    Command(("5000choyen", "5000兆"), make_5000choyen, 2),
    Command(("douyin", "dylogo"), make_douyin),
    Command(("google", "gglogo"), make_google),
]
