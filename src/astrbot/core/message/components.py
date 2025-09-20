"""
MIT License

Copyright (c) 2021 Lxns-Network

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import asyncio
import base64
import json
import os
from typing import Any
import uuid
from enum import Enum

from pydantic import BaseModel

from astrbot.core import astrbot_config, file_token_service, logger
from astrbot.core.utils.astrbot_path import get_astrbot_data_path
from astrbot.core.utils.io import download_file, download_image_by_url, file_to_base64


class ComponentType(str, Enum):
    Plain = "Plain"  # 纯文本消息
    Face = "Face"  # QQ表情
    Record = "Record"  # 语音
    Video = "Video"  # 视频
    At = "At"  # At
    Node = "Node"  # 转发消息的一个节点
    Nodes = "Nodes"  # 转发消息的多个节点
    Poke = "Poke"  # QQ 戳一戳
    Image = "Image"  # 图片
    Reply = "Reply"  # 回复
    Forward = "Forward"  # 转发消息
    File = "File"  # 文件

    RPS = "RPS"  # TODO
    Dice = "Dice"  # TODO
    Shake = "Shake"  # TODO
    Anonymous = "Anonymous"  # TODO
    Share = "Share"
    Contact = "Contact"  # TODO
    Location = "Location"  # TODO
    Music = "Music"
    RedBag = "RedBag"
    Xml = "Xml"
    Json = "Json"
    CardImage = "CardImage"
    TTS = "TTS"
    Unknown = "Unknown"

    WechatEmoji = "WechatEmoji"  # Wechat 下的 emoji 表情包

    # Discord 专用组件

    DiscordEmbed = "discord_embed"  # Discord 的 Embed 消息组件
    DiscordReference = "discord_reference"  # Discord 的引用组件
    DiscordView = "discord_view"  # Discord 的视图组件，包含按钮和选择菜单
    DiscordButton = "discord_button"  # Discord 的按钮组件


class BaseMessageComponent(BaseModel):
    type: ComponentType

    def toString(self):
        output = f"[CQ:{self.type.value.lower()}"
        for k, v in self.__dict__.items():
            if k == "type" or v is None:
                continue
            if k == "_type":
                k = "type"
            if isinstance(v, bool):
                v = 1 if v else 0
            output += ",%s=%s" % (
                k,
                str(v)
                .replace("&", "&amp;")
                .replace(",", "&#44;")
                .replace("[", "&#91;")
                .replace("]", "&#93;"),
            )
        output += "]"
        return output

    def toDict(self):
        data = {}
        for k, v in self.__dict__.items():
            if k == "type" or v is None:
                continue
            if k == "_type":
                k = "type"
            data[k] = v
        output: dict[str, str | Any] = {"type": self.type.value.lower(), "data": data}
        return output

    async def to_dict(self) -> dict[str, str | Any]:
        # 默认情况下，回退到旧的同步 toDict()
        return self.toDict()
    
class Plain(BaseMessageComponent):
    type: ComponentType = ComponentType.Plain
    text: str
    convert: bool | None = True  # 若为 False 则直接发送未转换 CQ 码的消息

    def __init__(self, text: str, convert: bool = True, **kwargs: Any):
        super().__init__(type=ComponentType.Plain, **kwargs)
        self.text = text
        self.convert = convert

    def toString(self):  # 没有 [CQ:plain] 这种东西，所以直接导出纯文本
        if not self.convert:
            return self.text
        return (
            self.text.replace("&", "&amp;").replace("[", "&#91;").replace("]", "&#93;")
        )

    def toDict(self):
        return {"type": "text", "data": {"text": self.text.strip()}}

    async def to_dict(self):
        return {"type": "text", "data": {"text": self.text}}


class Face(BaseMessageComponent):
    type: ComponentType = ComponentType.Face
    id: int

    def __init__(self, **kwargs: Any):
        super().__init__(type=ComponentType.Face, **kwargs)

class Record(BaseMessageComponent):
    type: ComponentType = ComponentType.Record
    file: str | None = ""
    magic: bool | None = False
    url: str | None = ""
    cache: bool | None = True
    proxy: bool | None = True
    timeout: int | None = 0
    # 额外
    path: str | None

    def __init__(self, file: str | None, **kwargs: Any):
        super().__init__(type=ComponentType.Record, **kwargs)
        self.file = file

    @staticmethod
    def fromFileSystem(path: str, **kwargs: Any) -> "Record":
        return Record(file=f"file:///{os.path.abspath(path)}", path=path, **kwargs)

    @staticmethod
    def fromURL(url: str, **kwargs: Any) -> "Record":
        if url.startswith("http://") or url.startswith("https://"):
            return Record(file=url, **kwargs)
        raise Exception("not a valid url")

    @staticmethod
    def fromBase64(bs64_data: str, **_):
        return Record(file=f"base64://{bs64_data}", **_)

    async def convert_to_file_path(self) -> str:
        """将这个语音统一转换为本地文件路径。这个方法避免了手动判断语音数据类型，直接返回语音数据的本地路径（如果是网络 URL, 则会自动进行下载）。

        Returns:
            str: 语音的本地路径，以绝对路径表示。
        """
        if not self.file:
            raise Exception(f"not a valid file: {self.file}")
        if self.file.startswith("file:///"):
            return self.file[8:]
        elif self.file.startswith("http"):
            file_path = await download_image_by_url(self.file)
            return os.path.abspath(file_path)
        elif self.file.startswith("base64://"):
            bs64_data = self.file.removeprefix("base64://")
            image_bytes = base64.b64decode(bs64_data)
            temp_dir = os.path.join(get_astrbot_data_path(), "temp")
            file_path = os.path.join(temp_dir, f"{uuid.uuid4()}.jpg")
            with open(file_path, "wb") as f:
                f.write(image_bytes)
            return os.path.abspath(file_path)
        elif os.path.exists(self.file):
            return os.path.abspath(self.file)
        else:
            raise Exception(f"not a valid file: {self.file}")

    async def convert_to_base64(self) -> str:
        """将语音统一转换为 base64 编码。这个方法避免了手动判断语音数据类型，直接返回语音数据的 base64 编码。

        Returns:
            str: 语音的 base64 编码，不以 base64:// 或者 data:image/jpeg;base64, 开头。
        """
        # convert to base64
        if not self.file:
            raise Exception(f"not a valid file: {self.file}")
        if self.file.startswith("file:///"):
            bs64_data = file_to_base64(self.file[8:])
        elif self.file.startswith("http"):
            file_path = await download_image_by_url(self.file)
            bs64_data = file_to_base64(file_path)
        elif self.file.startswith("base64://"):
            bs64_data = self.file
        elif os.path.exists(self.file):
            bs64_data = file_to_base64(self.file)
        else:
            raise Exception(f"not a valid file: {self.file}")
        bs64_data = bs64_data.removeprefix("base64://")
        return bs64_data

    async def register_to_file_service(self) -> str:
        """
        将语音注册到文件服务。

        Returns:
            str: 注册后的URL

        Raises:
            Exception: 如果未配置 callback_api_base
        """
        callback_host = astrbot_config.get("callback_api_base")

        if not callback_host:
            raise Exception("未配置 callback_api_base，文件服务不可用")

        file_path = await self.convert_to_file_path()

        token = await file_token_service.register_file(file_path)

        logger.debug(f"已注册：{callback_host}/api/file/{token}")

        return f"{callback_host}/api/file/{token}"
class Video(BaseMessageComponent):
    type: ComponentType = ComponentType.Video
    file: str
    cover: str | None = ""
    c: int | None = 2
    # 额外
    path: str | None = ""

    def __init__(self, file: str, **kwargs: Any):
        super().__init__(type=ComponentType.Video, **kwargs)
        self.file = file

    @staticmethod
    def fromFileSystem(path: str, **kwargs: Any) -> "Video":
        return Video(file=f"file:///{os.path.abspath(path)}", path=path, **kwargs)

    @staticmethod
    def fromURL(url: str, **kwargs: Any) -> "Video":
        if url.startswith("http://") or url.startswith("https://"):
            return Video(file=url, **kwargs)
        raise Exception("not a valid url")

    async def convert_to_file_path(self) -> str:
        """将这个视频统一转换为本地文件路径。这个方法避免了手动判断视频数据类型，直接返回视频数据的本地路径（如果是网络 URL，则会自动进行下载）。

        Returns:
            str: 视频的本地路径，以绝对路径表示。
        """
        url = self.file
        if url and url.startswith("file:///"):
            return url[8:]
        elif url and url.startswith("http"):
            download_dir = os.path.join(get_astrbot_data_path(), "temp")
            video_file_path = os.path.join(download_dir, f"{uuid.uuid4().hex}")
            await download_file(url, video_file_path)
            if os.path.exists(video_file_path):
                return os.path.abspath(video_file_path)
            else:
                raise Exception(f"download failed: {url}")
        elif os.path.exists(url):
            return os.path.abspath(url)
        else:
            raise Exception(f"not a valid file: {url}")

    async def register_to_file_service(self):
        """
        将视频注册到文件服务。

        Returns:
            str: 注册后的URL

        Raises:
            Exception: 如果未配置 callback_api_base
        """
        callback_host = astrbot_config.get("callback_api_base")

        if not callback_host:
            raise Exception("未配置 callback_api_base，文件服务不可用")

        file_path = await self.convert_to_file_path()

        token = await file_token_service.register_file(file_path)

        logger.debug(f"已注册：{callback_host}/api/file/{token}")

        return f"{callback_host}/api/file/{token}"

    async def to_dict(self):
        """需要和 toDict 区分开，toDict 是同步方法"""
        url_or_path = self.file
        if url_or_path.startswith("http"):
            payload_file = url_or_path
        elif callback_host := astrbot_config.get("callback_api_base"):
            callback_host = str(callback_host).removesuffix("/")
            token = await file_token_service.register_file(url_or_path)
            payload_file = f"{callback_host}/api/file/{token}"
            logger.debug(f"Generated video file callback link: {payload_file}")
        else:
            payload_file = url_or_path
        return {
            "type": "video",
            "data": {
                "file": payload_file,
            },
        }
class At(BaseMessageComponent):
    type: ComponentType = ComponentType.At
    qq: int | str  # 此处str为all时代表所有人
    name: str | None = ""

    def __init__(self, **kwargs: Any):
        super().__init__(type=ComponentType.At, **kwargs)

    def toDict(self):
        return {
            "type": "at",
            "data": {"qq": str(self.qq)},
        }
class AtAll(At):
    qq : int | str = "all"

    def __init__(self, **_):
        super().__init__(type=ComponentType.At, **_)

class RPS(BaseMessageComponent):  # TODO
    type: ComponentType = ComponentType.RPS

    def __init__(self, **_):
        super().__init__(type=ComponentType.RPS, **_)

class Dice(BaseMessageComponent):  # TODO
    type: ComponentType = ComponentType.Dice

    def __init__(self, **_):
        super().__init__(type=ComponentType.Dice, **_)

class Shake(BaseMessageComponent):  # TODO
    type: ComponentType = ComponentType.Shake

    def __init__(self, **_):
        super().__init__(type=ComponentType.Shake, **_)

class Anonymous(BaseMessageComponent):  # TODO
    type: ComponentType = ComponentType.Anonymous
    ignore: bool | None = False

    def __init__(self, **_):
        super().__init__(type=ComponentType.Anonymous, **_)


class Share(BaseMessageComponent):
    type: ComponentType = ComponentType.Share
    url: str
    title: str
    content: str | None = ""
    image: str | None = ""

    def __init__(self, **_):
        super().__init__(**_)


class Contact(BaseMessageComponent):  # TODO
    type: ComponentType = ComponentType.Contact
    _type: str  # type 字段冲突
    id: int | None = 0

    def __init__(self, **_):
        super().__init__(**_)


class Location(BaseMessageComponent):  # TODO
    type: ComponentType = ComponentType.Location
    lat: float
    lon: float
    title: str | None = ""
    content: str | None = ""

    def __init__(self, **_):
        super().__init__(**_)


class Music(BaseMessageComponent):
    type: ComponentType = ComponentType.Music
    _type: str
    id: int | None = 0
    url: str | None = ""
    audio: str | None = ""
    title: str | None = ""
    content: str | None = ""
    image: str | None = ""

    def __init__(self, **_):
        # for k in _.keys():
        #     if k == "_type" and _[k] not in ["qq", "163", "xm", "custom"]:
        #         logger.warn(f"Protocol: {k}={_[k]} doesn't match values")
        super().__init__(**_)


class Image(BaseMessageComponent):
    type: ComponentType = ComponentType.Image
    file: str | None = ""
    _type: str | None = ""
    subType: int | None = 0
    url: str | None = ""
    cache: bool | None = True
    id: int | None = 40000
    c: int | None = 2
    # 额外
    path: str | None = ""
    file_unique: str | None = ""  # 某些平台可能有图片缓存的唯一标识

    def __init__(self, file: str | None, **_):
        super().__init__(type=ComponentType.Image, **_)
        self.file = file

    @staticmethod
    def fromURL(url: str, **_):
        if url.startswith("http://") or url.startswith("https://"):
            return Image(file=url, **_)
        raise Exception("not a valid url")

    @staticmethod
    def fromFileSystem(path, **_):
        return Image(file=f"file:///{os.path.abspath(path)}", path=path, **_)

    @staticmethod
    def fromBase64(base64: str, **_):
        return Image(f"base64://{base64}", **_)

    @staticmethod
    def fromBytes(byte: bytes):
        return Image.fromBase64(base64.b64encode(byte).decode())

    @staticmethod
    def fromIO(IO):
        return Image.fromBytes(IO.read())

    async def convert_to_file_path(self) -> str:
        """将这个图片统一转换为本地文件路径。这个方法避免了手动判断图片数据类型，直接返回图片数据的本地路径（如果是网络 URL, 则会自动进行下载）。

        Returns:
            str: 图片的本地路径，以绝对路径表示。
        """
        url = self.url or self.file
        if not url:
            raise ValueError("No valid file or URL provided")
        if url.startswith("file:///"):
            return url[8:]
        elif url.startswith("http"):
            image_file_path = await download_image_by_url(url)
            return os.path.abspath(image_file_path)
        elif url.startswith("base64://"):
            bs64_data = url.removeprefix("base64://")
            image_bytes = base64.b64decode(bs64_data)
            temp_dir = os.path.join(get_astrbot_data_path(), "temp")
            image_file_path = os.path.join(temp_dir, f"{uuid.uuid4()}.jpg")
            with open(image_file_path, "wb") as f:
                f.write(image_bytes)
            return os.path.abspath(image_file_path)
        elif os.path.exists(url):
            return os.path.abspath(url)
        else:
            raise Exception(f"not a valid file: {url}")

    async def convert_to_base64(self) -> str:
        """将这个图片统一转换为 base64 编码。这个方法避免了手动判断图片数据类型，直接返回图片数据的 base64 编码。

        Returns:
            str: 图片的 base64 编码，不以 base64:// 或者 data:image/jpeg;base64, 开头。
        """
        # convert to base64
        url = self.url or self.file
        if not url:
            raise ValueError("No valid file or URL provided")
        if url.startswith("file:///"):
            bs64_data = file_to_base64(url[8:])
        elif url.startswith("http"):
            image_file_path = await download_image_by_url(url)
            bs64_data = file_to_base64(image_file_path)
        elif url.startswith("base64://"):
            bs64_data = url
        elif os.path.exists(url):
            bs64_data = file_to_base64(url)
        else:
            raise Exception(f"not a valid file: {url}")
        bs64_data = bs64_data.removeprefix("base64://")
        return bs64_data

    async def register_to_file_service(self) -> str:
        """
        将图片注册到文件服务。

        Returns:
            str: 注册后的URL

        Raises:
            Exception: 如果未配置 callback_api_base
        """
        callback_host = astrbot_config.get("callback_api_base")

        if not callback_host:
            raise Exception("未配置 callback_api_base，文件服务不可用")

        file_path = await self.convert_to_file_path()

        token = await file_token_service.register_file(file_path)

        logger.debug(f"已注册：{callback_host}/api/file/{token}")

        return f"{callback_host}/api/file/{token}"


class Reply(BaseMessageComponent):
    type: ComponentType = ComponentType.Reply
    id: str | int
    """所引用的消息 ID"""
    chain: list["BaseMessageComponent"] | None = []
    """被引用的消息段列表"""
    sender_id: int | str | None = 0
    """被引用的消息对应的发送者的 ID"""
    sender_nickname: str | None = ""
    """被引用的消息对应的发送者的昵称"""
    time: int | None = 0
    """被引用的消息发送时间"""
    message_str: str | None = ""
    """被引用的消息解析后的纯文本消息字符串"""

    text: str | None = ""
    """deprecated"""
    qq: int | None = 0
    """deprecated"""
    seq: int | None = 0
    """deprecated"""

    def __init__(self, **_):
        super().__init__(**_)


class RedBag(BaseMessageComponent):
    type: ComponentType = ComponentType.RedBag
    title: str

    def __init__(self, **_):
        super().__init__(**_)


class Poke(BaseMessageComponent):
    type: ComponentType = ComponentType.Poke
    id: int | None = 0
    qq: int | None = 0

    def __init__(self, poke_type: str, **_):
        super().__init__(type=ComponentType.Poke, **_)
        # Store the poke type as an attribute instead of modifying the enum type
        self.poke_type = poke_type


class Forward(BaseMessageComponent):
    type: ComponentType = ComponentType.Forward
    id: str

    def __init__(self, **_):
        super().__init__(**_)


class Node(BaseMessageComponent):
    """群合并转发消息"""

    type: ComponentType = ComponentType.Node
    id: int | None = 0  # 忽略
    name: str | None = ""  # qq昵称
    uin: str | None = "0"  # qq号
    content: list[BaseMessageComponent] | None = []
    seq: str | list[str] | None = ""  # 忽略
    time: int | None = 0  # 忽略

    def __init__(self, content: list[BaseMessageComponent], **_):
        if isinstance(content, Node):
            # back
            content = [content]
        super().__init__(type=ComponentType.Node, **_)
        self.content = content

    async def to_dict(self):
        data_content = []
        # Check if content is not None before iterating
        if self.content:
            for comp in self.content:
                if isinstance(comp, (Image, Record)):
                    # For Image and Record segments, we convert them to base64
                    bs64 = await comp.convert_to_base64()
                    data_content.append(
                        {
                            "type": comp.type.value.lower(),
                            "data": {"file": f"base64://{bs64}"},
                        }
                    )
                elif isinstance(comp, Plain):
                    # For Plain segments, we need to handle the plain differently
                    d = await comp.to_dict()
                    data_content.append(d)
                elif isinstance(comp, File):
                    # For File segments, we need to handle the file differently
                    d = await comp.to_dict()
                    data_content.append(d)
                elif isinstance(comp, (Node, Nodes)):
                    # For Node segments, we recursively convert them to dict
                    d = await comp.to_dict()
                    data_content.append(d)
                else:
                    d = comp.toDict()
                    data_content.append(d)
        return {
            "type": "node",
            "data": {
                "user_id": str(self.uin),
                "nickname": self.name,
                "content": data_content,
            },
        }


class Nodes(BaseMessageComponent):
    type: ComponentType = ComponentType.Nodes
    nodes: list[Node]

    def __init__(self, nodes: list[Node], **_):
        super().__init__(nodes=nodes, **_)

    def toDict(self):
        """Deprecated. Use to_dict instead"""
        ret = {
            "messages": [],
        }
        for node in self.nodes:
            d = node.toDict()
            ret["messages"].append(d)
        return ret

    async def to_dict(self):
        """将 Nodes 转换为字典格式，适用于 OneBot JSON 格式"""
        ret = {"messages": []}
        for node in self.nodes:
            d = await node.to_dict()
            ret["messages"].append(d)
        return ret


class Xml(BaseMessageComponent):
    type: ComponentType = ComponentType.Xml
    data: str
    resid: int | None = 0

    def __init__(self, **_):
        super().__init__(**_)


class Json(BaseMessageComponent):
    type: ComponentType = ComponentType.Json
    data: str | dict
    resid: int | None = 0

    def __init__(self, data, **_):
        if isinstance(data, dict):
            data = json.dumps(data)
        super().__init__(data=data, **_)


class CardImage(BaseMessageComponent):
    type: ComponentType = ComponentType.CardImage
    file: str
    cache: bool | None = True
    minwidth: int | None = 400
    minheight: int | None = 400
    maxwidth: int | None = 500
    maxheight: int | None = 500
    source: str | None = ""
    icon: str | None = ""

    def __init__(self, **_):
        super().__init__(**_)

    @staticmethod
    def fromFileSystem(path, **_):
        return CardImage(file=f"file:///{os.path.abspath(path)}", **_)


class TTS(BaseMessageComponent):
    type: ComponentType = ComponentType.TTS
    text: str

    def __init__(self, **_):
        super().__init__(type=ComponentType.TTS, **_)


class Unknown(BaseMessageComponent):
    type: ComponentType = ComponentType.Unknown
    text: str

    def toString(self):
        return ""


class File(BaseMessageComponent):
    """
    文件消息段
    """

    type: ComponentType = ComponentType.File
    name: str | None = ""  # 名字
    file_: str | None = ""  # 本地路径
    url: str | None = ""  # url

    def __init__(self, name: str, file: str = "", url: str = ""):
        """文件消息段。"""
        super().__init__(type=ComponentType.File)
        self.name = name
        self.file_ = file
        self.url = url
    @property
    def file(self) -> str:
        """
        获取文件路径，如果文件不存在但有URL，则同步下载文件

        Returns:
            str: 文件路径
        """
        if self.file_ and os.path.exists(self.file_):
            return os.path.abspath(self.file_)

        if self.url:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    logger.warning(
                        (
                            "不可以在异步上下文中同步等待下载! "
                            "这个警告通常发生于某些逻辑试图通过 <File>.file 获取文件消息段的文件内容。"
                            "请使用 await get_file() 代替直接获取 <File>.file 字段"
                        )
                    )
                    return ""
                else:
                    # 等待下载完成
                    loop.run_until_complete(self._download_file())

                    if self.file_ and os.path.exists(self.file_):
                        return os.path.abspath(self.file_)
            except Exception as e:
                logger.error(f"文件下载失败: {e}")

        return ""

    @file.setter
    def file(self, value: str):
        """
        向前兼容, 设置file属性, 传入的参数可能是文件路径或URL

        Args:
            value (str): 文件路径或URL
        """
        if value.startswith("http://") or value.startswith("https://"):
            self.url = value
        else:
            self.file_ = value

    async def get_file(self, allow_return_url: bool = False) -> str:
        """异步获取文件。请注意在使用后清理下载的文件, 以免占用过多空间

        Args:
            allow_return_url: 是否允许以文件 http 下载链接的形式返回，这允许您自行控制是否需要下载文件。
            注意，如果为 True，也可能返回文件路径。
        Returns:
            str: 文件路径或者 http 下载链接
        """
        if allow_return_url and self.url:
            return self.url

        if self.file_ and os.path.exists(self.file_):
            return os.path.abspath(self.file_)

        if self.url:
            await self._download_file()
            return os.path.abspath(self.file_)

        return ""

    async def _download_file(self):
        """下载文件"""
        download_dir = os.path.join(get_astrbot_data_path(), "temp")
        os.makedirs(download_dir, exist_ok=True)
        file_path = os.path.join(download_dir, f"{uuid.uuid4().hex}")
        await download_file(self.url, file_path)
        self.file_ = os.path.abspath(file_path)

    async def register_to_file_service(self):
        """
        将文件注册到文件服务。

        Returns:
            str: 注册后的URL

        Raises:
            Exception: 如果未配置 callback_api_base
        """
        callback_host = astrbot_config.get("callback_api_base")

        if not callback_host:
            raise Exception("未配置 callback_api_base，文件服务不可用")

        file_path = await self.get_file()

        token = await file_token_service.register_file(file_path)

        logger.debug(f"已注册：{callback_host}/api/file/{token}")

        return f"{callback_host}/api/file/{token}"

    async def to_dict(self):
        """需要和 toDict 区分开，toDict 是同步方法"""
        url_or_path = await self.get_file(allow_return_url=True)
        if url_or_path.startswith("http"):
            payload_file = url_or_path
        elif callback_host := astrbot_config.get("callback_api_base"):
            callback_host = str(callback_host).removesuffix("/")
            token = await file_token_service.register_file(url_or_path)
            payload_file = f"{callback_host}/api/file/{token}"
            logger.debug(f"Generated file callback link: {payload_file}")
        else:
            payload_file = url_or_path
        return {
            "type": "file",
            "data": {
                "name": self.name,
                "file": payload_file,
            },
        }


class WechatEmoji(BaseMessageComponent):
    type: ComponentType = ComponentType.WechatEmoji
    md5: str | None = ""
    md5_len: int | None = 0
    cdnurl: str | None = ""

    def __init__(self, **_):
        super().__init__(**_)


ComponentTypes = {
    "plain": Plain,
    "text": Plain,
    "face": Face,
    "record": Record,
    "video": Video,
    "at": At,
    "rps": RPS,
    "dice": Dice,
    "shake": Shake,
    "anonymous": Anonymous,
    "share": Share,
    "contact": Contact,
    "location": Location,
    "music": Music,
    "image": Image,
    "reply": Reply,
    "redbag": RedBag,
    "poke": Poke,
    "forward": Forward,
    "node": Node,
    "nodes": Nodes,
    "xml": Xml,
    "json": Json,
    "cardimage": CardImage,
    "tts": TTS,
    "unknown": Unknown,
    "file": File,
    "WechatEmoji": WechatEmoji,
}


__all__ = [
    "ComponentType",
    "BaseMessageComponent",
    "Plain",
    "Face",
    "Record",
    "Video",
    "At",
    "AtAll",
    "RPS",
    "Dice",
    "Shake",
    "Anonymous",
    "Share",
    "Contact",
    "Location",
    "Music",
    "Image",
    "Reply",
    "RedBag",
    "Poke",
    "Forward",
    "Node",
    "Nodes",
    "Xml",
    "Json",
    "CardImage",
    "TTS",
    "Unknown",
    "File",
    "WechatEmoji",
    "ComponentTypes",
]