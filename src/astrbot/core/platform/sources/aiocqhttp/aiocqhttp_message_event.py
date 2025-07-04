import asyncio
import re
from typing import AsyncGenerator, Dict, List
from aiocqhttp import CQHttp
from astrbot.api.event import AstrMessageEvent, MessageChain
from astrbot.api.message_components import (
    Image,
    Node,
    Nodes,
    Plain,
    Record,
    Video,
    File,
    BaseMessageComponent,
)
from astrbot.api.platform import Group, MessageMember


class AiocqhttpMessageEvent(AstrMessageEvent):
    def __init__(
        self, message_str, message_obj, platform_meta, session_id, bot: CQHttp
    ):
        super().__init__(message_str, message_obj, platform_meta, session_id)
        self.bot = bot

    @staticmethod
    async def _from_segment_to_dict(segment: BaseMessageComponent) -> dict:
        """修复部分字段"""
        if isinstance(segment, (Image, Record)):
            # For Image and Record segments, we convert them to base64
            bs64 = await segment.convert_to_base64()
            return {
                "type": segment.type.lower(),
                "data": {
                    "file": f"base64://{bs64}",
                },
            }
        elif isinstance(segment, File):
            # For File segments, we need to handle the file differently
            d = await segment.to_dict()
            return d
        elif isinstance(segment, Video):
            d = await segment.to_dict()
            return d
        else:
            # For other segments, we simply convert them to a dict by calling toDict
            return segment.toDict()

    @staticmethod
    async def _parse_onebot_json(message_chain: MessageChain):
        """解析成 OneBot json 格式"""
        ret = []
        for segment in message_chain.chain:
            if isinstance(segment, Plain):
                if not segment.text.strip():
                    continue
            d = await AiocqhttpMessageEvent._from_segment_to_dict(segment)
            ret.append(d)
        return ret

    async def send(self, message: MessageChain):
        # 转发消息、文件消息不能和普通消息混在一起发送
        send_one_by_one = any(
            isinstance(seg, (Node, Nodes, File)) for seg in message.chain
        )
        if send_one_by_one:
            for seg in message.chain:
                if isinstance(seg, (Node, Nodes)):
                    # 合并转发消息

                    if isinstance(seg, Node):
                        nodes = Nodes([seg])
                        seg = nodes

                    payload = await seg.to_dict()

                    if self.get_group_id():
                        payload["group_id"] = self.get_group_id()
                        await self.bot.call_action("send_group_forward_msg", **payload)
                    else:
                        payload["user_id"] = self.get_sender_id()
                        await self.bot.call_action(
                            "send_private_forward_msg", **payload
                        )                
                elif isinstance(seg, File):
                    d = await AiocqhttpMessageEvent._from_segment_to_dict(seg)
                    # 根据消息类型使用对应的API方法发送文件
                    if self.get_group_id():
                        await self.bot.send_group_msg(group_id=int(self.get_group_id()), message=[d])
                    else:
                        await self.bot.send_private_msg(user_id=int(self.get_sender_id()), message=[d])
                else:
                    # 根据消息类型使用对应的API方法发送其他消息
                    msg = await AiocqhttpMessageEvent._parse_onebot_json(MessageChain([seg]))
                    if self.get_group_id():
                        await self.bot.send_group_msg(group_id=int(self.get_group_id()), message=msg)
                    else:
                        await self.bot.send_private_msg(user_id=int(self.get_sender_id()), message=msg)
                    await asyncio.sleep(0.5)
        
        else:
            ret = await AiocqhttpMessageEvent._parse_onebot_json(message)
            if not ret:
                return
              # 根据消息类型使用对应的API方法
            if self.get_group_id():
                await self.bot.send_group_msg(group_id=int(self.get_group_id()), message=ret)
            else:
                await self.bot.send_private_msg(user_id=int(self.get_sender_id()), message=ret)

        await super().send(message)

    async def send_streaming(
        self, generator: AsyncGenerator, use_fallback: bool = False
    ):
        if not use_fallback:
            buffer = None
            async for chain in generator:
                if not buffer:
                    buffer = chain
                else:
                    buffer.chain.extend(chain.chain)
            if not buffer:
                return
            buffer.squash_plain()
            await self.send(buffer)
            return await super().send_streaming(generator, use_fallback)

        buffer = ""
        pattern = re.compile(r"[^。？！~…]+[。？！~…]+")

        async for chain in generator:
            if isinstance(chain, MessageChain):
                for comp in chain.chain:
                    if isinstance(comp, Plain):
                        buffer += comp.text
                        if any(p in buffer for p in "。？！~…"):
                            buffer = await self.process_buffer(buffer, pattern)
                    else:
                        await self.send(MessageChain(chain=[comp]))
                        await asyncio.sleep(1.5)  # 限速

        if buffer.strip():
            await self.send(MessageChain([Plain(buffer)]))
        return await super().send_streaming(generator, use_fallback)

    async def get_group(self, group_id=None, **kwargs):
        if isinstance(group_id, str) and group_id.isdigit():
            group_id = int(group_id)
        elif self.get_group_id():
            group_id = int(self.get_group_id())
        else:
            return None

        info: dict = await self.bot.call_action(
            "get_group_info",
            group_id=group_id,
        )

        members: List[Dict] = await self.bot.call_action(
            "get_group_member_list",
            group_id=group_id,
        )

        owner_id = None
        admin_ids = []
        for member in members:
            if member["role"] == "owner":
                owner_id = member["user_id"]
            if member["role"] == "admin":
                admin_ids.append(member["user_id"])

        group = Group(
            group_id=str(group_id),
            group_name=info.get("group_name"),
            group_avatar="",
            group_admins=admin_ids,
            group_owner=str(owner_id),
            members=[
                MessageMember(
                    user_id=member["user_id"],
                    nickname=member.get("nickname") or member.get("card"),
                )
                for member in members
            ],
        )

        return group
