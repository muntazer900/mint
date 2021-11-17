# Copyright (C) 2021 By Veez Music-Project
# Commit Start Date 20/10/2021
# Finished On 28/10/2021

import asyncio
import re

from config import ASSISTANT_NAME, BOT_USERNAME, IMG_1, IMG_2
from driver.filters import command, other_filters
from driver.queues import QUEUE, add_to_queue
from driver.veez import call_py, user
from pyrogram import Client
from pyrogram.errors import UserAlreadyParticipant, UserNotParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pytgcalls import StreamType
from pytgcalls.types.input_stream import AudioVideoPiped
from pytgcalls.types.input_stream.quality import (
    HighQualityAudio,
    HighQualityVideo,
    LowQualityVideo,
    MediumQualityVideo,
)
from youtubesearchpython import VideosSearch


def ytsearch(query):
    try:
        search = VideosSearch(query, limit=1)
        for r in search.result()["result"]:
            ytid = r["id"]
            if len(r["title"]) > 34:
                songname = r["title"][:70]
            else:
                songname = r["title"]
            url = f"https://www.youtube.com/watch?v={ytid}"
        return [songname, url]
    except Exception as e:
        print(e)
        return 0


async def ytdl(link):
    proc = await asyncio.create_subprocess_exec(
        "yt-dlp",
        "-g",
        "-f",
        "best[height<=?720][width<=?1280]",
        f"{link}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if stdout:
        return 1, stdout.decode().split("\n")[0]
    else:
        return 0, stderr.decode()


@Client.on_message(command(["فيديو", f"vplay@{BOT_USERNAME}"]) & other_filters)
async def vplay(c: Client, m: Message):
    replied = m.reply_to_message
    chat_id = m.chat.id
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(text="• تحكم", callback_data="cbmenu"),
                InlineKeyboardButton(text="• اغلاق", callback_data="cls"),
            ]
        ]
    )
    if m.sender_chat:
        return await m.reply_text("انت __مستخدم مجهول م اعرفك__ !\n\n» لازم مشرف ياعيني حته اتاكد منك.")
    try:
        aing = await c.get_me()
    except Exception as e:
        return await m.reply_text(f"error:\n\n{e}")
    a = await c.get_chat_member(chat_id, aing.id)
    if a.status != "administrator":
        await m.reply_text(
            f"💡 لاستخدامي احتاج ان اكون  **مشرفا في مجموعتك** وبعد ذالك **امنحني الصلاحيات التالية**:\n\n» ❌ __ حذف رسائل الحلوين__\n» ❌ __حظر المستخدمين بلنعال__\n» ❌ __اضافه مستخدمين حلوين__\n» ❌ __بعد ان تمنحني الصلاحيات اكتب__\n\nData is **.تحديث** سيتم تحديث البيانات  **تلقائيا**"
        )
        return
    if not a.can_manage_voice_chats:
        await m.reply_text(
            "ياعيني كتلك انطيني هاي الصلاحية ليش تصير غبي؟:" + "\n\n» ❌ __ادارة المحادثات الصوتية__"
        )
        return
    if not a.can_delete_messages:
        await m.reply_text(
            "ياعيني كتلك انطيني هاي الصلاحية ليش تصير غبي؟:" + "\n\n» ❌ __حذف رسائل الحلوين__"
        )
        return
    if not a.can_invite_users:
        await m.reply_text("ياعيني كتلك انطيني هاي الصلاحية ليش تصير غبي؟:" + "\n\n» ❌ __اضافة مستخدمين حلوين__")
        return
    if not a.can_restrict_members:
        await m.reply_text("ياعيني كتلك انطيني هاي الصلاحية ليش تصير غبي؟:" + "\n\n» ❌ __حظر المستخدمين بلنعال__")
        return
    try:
        ubot = await user.get_me()
        b = await c.get_chat_member(chat_id, ubot.id)
        if b.status == "kicked":
            await m.reply_text(
                f"@{ASSISTANT_NAME} **ياعيني حساب المساعد محظور من المجموعة** {m.chat.title}\n\n» **واحد من مشرفينكم الخرا حظره , ف فك الحظر عنه وبعدها اكتب .انضم.**"
            )
            return
    except UserNotParticipant:
        if m.chat.username:
            try:
                await user.join_chat(m.chat.username)
            except Exception as e:
                await m.reply_text(f"❌ **فشل حساب المساعد في الانضمام**\n\n**السبب**: `{e}`")
                return
        else:
            try:
                pope = await c.export_chat_invite_link(chat_id)
                pepo = await c.revoke_chat_invite_link(chat_id, pope)
                await user.join_chat(pepo.invite_link)
            except UserAlreadyParticipant:
                pass
            except Exception as e:
                return await m.reply_text(
                    f"❌ **فشل حساب المساعد في الانضمام**\n\n**السبب**: `{e}`"
                )

    if replied:
        if replied.video or replied.document:
            loser = await replied.reply("📥 **جاري التحميل يعيني...**")
            dl = await replied.download()
            link = replied.link
            if len(m.command) < 2:
                Q = 720
            else:
                pq = m.text.split(None, 1)[1]
                if pq == "720" or "480" or "360":
                    Q = int(pq)
                else:
                    Q = 720
                    await loser.edit(
                        "» __only 720, 480, 360 allowed__ \n💡 **الان يتم البث بدقة 720p**"
                    )
            try:
                if replied.video:
                    songname = replied.video.file_name[:70]
                elif replied.document:
                    songname = replied.document.file_name[:70]
            except BaseException:
                songname = "Video"

            if chat_id in QUEUE:
                pos = add_to_queue(chat_id, songname, dl, link, "Video", Q)
                await loser.delete()
                requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                await m.reply_photo(
                    photo=f"{IMG_1}",
                    caption=f"💡 **يالله تم حشغلها وره هاي »** `{pos}`\n\n🏷 **الاسم:** [{songname}]({link})\n💭 **الدردشة:** `{chat_id}`\n🎧 **طلب من:** {requester}",
                    reply_markup=keyboard,
                )
            else:
                if Q == 720:
                    amaze = HighQualityVideo()
                elif Q == 480:
                    amaze = MediumQualityVideo()
                elif Q == 360:
                    amaze = LowQualityVideo()
                await call_py.join_group_call(
                    chat_id,
                    AudioVideoPiped(
                        dl,
                        HighQualityAudio(),
                        amaze,
                    ),
                    stream_type=StreamType().local_stream,
                )
                add_to_queue(chat_id, songname, dl, link, "فيديو", Q)
                await loser.delete()
                requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                await m.reply_photo(
                    photo=f"{IMG_2}",
                    caption=f"💡 **يالله تم شغلتها يعيوني.**\n\n🏷 **الاسم:** [{songname}]({link})\n💭 **الدردشة:** `{chat_id}`\n💡 **الحالة:** `مشغل طبيعي`\n🎧 **طلب من:** {requester}",
                    reply_markup=keyboard,
                )
        else:
            if len(m.command) < 2:
                await m.reply(
                    "» يخي لتصير غبي **هذا الامر** رد **على مقطع فيديو او انطيني شي خلبحث عليه ياحماري.**"
                )
            else:
                loser = await m.reply("🔎 **جاري البحث...**")
                query = m.text.split(None, 1)[1]
                search = ytsearch(query)
                Q = 720
                amaze = HighQualityVideo()
                if search == 0:
                    await loser.edit("❌ **بحثت ومالكيت شي دعبل عنخلقتي.**")
                else:
                    songname = search[0]
                    url = search[1]
                    veez, ytlink = await ytdl(url)
                    if veez == 0:
                        await loser.edit(f"❌ تم اكتشاف مشاكل yt-dl\n\n» `{ytlink}`")
                    else:
                        if chat_id in QUEUE:
                            pos = add_to_queue(
                                chat_id, songname, ytlink, url, "Video", Q
                            )
                            await loser.delete()
                            requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                            await m.reply_photo(
                                photo=f"{IMG_1}",
                                caption=f"💡 **يالله تم حشغلها وره هاي »** `{pos}`\n\n🏷 **الاسم:** [{songname}]({url})\n💭 **الدردشة:** `{chat_id}`\n🎧 **طلب من:** {requester}",
                                reply_markup=keyboard,
                            )
                        else:
                            try:
                                await call_py.join_group_call(
                                    chat_id,
                                    AudioVideoPiped(
                                        ytlink,
                                        HighQualityAudio(),
                                        amaze,
                                    ),
                                    stream_type=StreamType().local_stream,
                                )
                                add_to_queue(chat_id, songname, ytlink, url, "Video", Q)
                                await loser.delete()
                                requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                                await m.reply_photo(
                                    photo=f"{IMG_2}",
                                    caption=f"💡 **يالله تم شغلتها وانا خادم.**\n\n🏷 **الاسم:** [{songname}]({url})\n💭 **الدردشة:** `{chat_id}`\n💡 **الحالة:** `مشغل طبيعي`\n🎧 **طلب من:** {requester}",
                                    reply_markup=keyboard,
                                )
                            except Exception as ep:
                                await loser.delete()
                                await m.reply_text(f"🚫 error: `{ep}`")

    else:
        if len(m.command) < 2:
            await m.reply(
                "» لتصير غبي حبي **ملف فيديو**رد ع **او انطيني شي خلبحث عليه.**"
            )
        else:
            loser = await m.reply("🔎 **جاري البحث يعيني...**")
            query = m.text.split(None, 1)[1]
            search = ytsearch(query)
            Q = 720
            amaze = HighQualityVideo()
            if search == 0:
                await loser.edit("❌ **دعبل بحثت ومالكيت شي.**")
            else:
                songname = search[0]
                url = search[1]
                veez, ytlink = await ytdl(url)
                if veez == 0:
                    await loser.edit(f"❌تم اكتشاف مشاكل yt-dl\n\n» `{ytlink}`")
                else:
                    if chat_id in QUEUE:
                        pos = add_to_queue(chat_id, songname, ytlink, url, "Video", Q)
                        await loser.delete()
                        requester = (
                            f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                        )
                        await m.reply_photo(
                            photo=f"{IMG_1}",
                            caption=f"💡 **يالله تم حشغلها وره هاي »** `{pos}`\n\n🏷 **الاسم:** [{songname}]({url})\n💭 **الدردشة:** `{chat_id}`\n🎧 **طلب من:** {requester}",
                            reply_markup=keyboard,
                        )
                    else:
                        try:
                            await call_py.join_group_call(
                                chat_id,
                                AudioVideoPiped(
                                    ytlink,
                                    HighQualityAudio(),
                                    amaze,
                                ),
                                stream_type=StreamType().local_stream,
                            )
                            add_to_queue(chat_id, songname, ytlink, url, "Video", Q)
                            await loser.delete()
                            requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                            await m.reply_photo(
                                photo=f"{IMG_2}",
                                caption=f"💡 **يالله تم شغلتها عيوني.**\n\n🏷 **الاسم:** [{songname}]({url})\n💭 **الدردشة:** `{chat_id}`\n💡 **الحالة:** `مشغل طبيعي`\n🎧 **طلب من:** {requester}",
                                reply_markup=keyboard,
                            )
                        except Exception as ep:
                            await loser.delete()
                            await m.reply_text(f"🚫 error: `{ep}`")


@Client.on_message(command(["مباشر", f"vstream@{BOT_USERNAME}"]) & other_filters)
async def vstream(c: Client, m: Message):
    m.reply_to_message
    chat_id = m.chat.id
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(text="• تحكم", callback_data="cbmenu"),
                InlineKeyboardButton(text="• اغلاق", callback_data="cls"),
            ]
        ]
    )
    if m.sender_chat:
        return await m.reply_text("انت مستخدم مجول __يعني  م اعرفك__ !\n\n» لازم تكون مشرف حته اتاكد منك !.")
    try:
        aing = await c.get_me()
    except Exception as e:
        return await m.reply_text(f"error:\n\n{e}")
    a = await c.get_chat_member(chat_id, aing.id)
    if a.status != "administrator":
        await m.reply_text(
            f"💡ياعيني لاستخدامي احتاج **اكون مشرفا في مجموعتك** بعد ذالك **امنحني الصلاحيات التالية**:\n\n» ❌ __حذف رسائل الحلوين__\n» ❌ __حظر المستخدمين بلنعال__\n» ❌ __اضافة مستخدمين حلوين__\n» ❌ __ادارة المحادثات الصوتية__\n\nبعد ذالك اكتب **.تحديث** سيتم تحديث البيانات تلقائيا **يلا**"
        )
        return
    if not a.can_manage_voice_chats:
        await m.reply_text(
            "لتصير غبي مو كتلك انطيني هاي لصلاحية:" + "\n\n» ❌ __ادارة المحادثات الصوتية__"
        )
        return
    if not a.can_delete_messages:
        await m.reply_text(
            "لتصير غبي مو كتلك انطيني هاي لصلاحية:" + "\n\n» ❌ __حذف الرسائل__"
        )
        return
    if not a.can_invite_users:
        await m.reply_text("لتصير غبي مو كتلك انطيني هاي لصلاحية:" + "\n\n» ❌ __اضافة مستخدمين__")
        return
    if not a.can_restrict_members:
        await m.reply_text("لتصير غبي مو كتلك انطيني هاي لصلاحية:" + "\n\n» ❌ __حظر المستخدمين__")
        return
    try:
        ubot = await user.get_me()
        b = await c.get_chat_member(chat_id, ubot.id)
        if b.status == "kicked":
            await m.reply_text(
                f"@{ASSISTANT_NAME} **ياعيني حساب المساعد محظور من المجموعة** {m.chat.title}\n\n» **واحد من مشرفينكم حاظره , قم بالغاء الحظر وبعد ذاك اكتب .انضم.**"
            )
            return
    except UserNotParticipant:
        if m.chat.username:
            try:
                await user.join_chat(m.chat.username)
            except Exception as e:
                await m.reply_text(f"❌ **فشل حساب المساعد باللانضما هنا**\n\n**السبب**: `{e}`")
                return
        else:
            try:
                pope = await c.export_chat_invite_link(chat_id)
                pepo = await c.revoke_chat_invite_link(chat_id, pope)
                await user.join_chat(pepo.invite_link)
            except UserAlreadyParticipant:
                pass
            except Exception as e:
                return await m.reply_text(
                    f"❌ **فشل حساب المساعد بالانضمام هنا**\n\n**السبب**: `{e}`"
                )

    if len(m.command) < 2:
        await m.reply("»أعطني رابط مباشر / رابط m3u8 url / youtube لتشغيل.")
    else:
        if len(m.command) == 2:
            link = m.text.split(None, 1)[1]
            Q = 720
            loser = await m.reply("🔄 **جاري المعالجة يعيوني...**")
        elif len(m.command) == 3:
            op = m.text.split(None, 1)[1]
            link = op.split(None, 1)[0]
            quality = op.split(None, 1)[1]
            if quality == "720" or "480" or "360":
                Q = int(quality)
            else:
                Q = 720
                await m.reply(
                    "» __only 720, 480, 360 allowed__ \n💡 **الان يتم البث بدقة 720p**"
                )
            loser = await m.reply("🔄 **جاري المعالجة ياعيني...**")
        else:
            await m.reply("**.مباشر {link} {720/480/360}**")

        regex = r"^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+"
        match = re.match(regex, link)
        if match:
            veez, livelink = await ytdl(link)
        else:
            livelink = link
            veez = 1

        if veez == 0:
            await loser.edit(f"❌ تم اكتشاف مشاكل yt-dl\n\n» `{ytlink}`")
        else:
            if chat_id in QUEUE:
                pos = add_to_queue(chat_id, "Live Stream", livelink, link, "Video", Q)
                await loser.delete()
                requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                await m.reply_photo(
                    photo=f"{IMG_1}",
                    caption=f"💡 **يالله تم حشغلها وره هاي »** `{pos}`\n\n💭 **الدردشة:** `{chat_id}`\n🎧 **طلب من:** {requester}",
                    reply_markup=keyboard,
                )
            else:
                if Q == 720:
                    amaze = HighQualityVideo()
                elif Q == 480:
                    amaze = MediumQualityVideo()
                elif Q == 360:
                    amaze = LowQualityVideo()
                try:
                    await call_py.join_group_call(
                        chat_id,
                        AudioVideoPiped(
                            livelink,
                            HighQualityAudio(),
                            amaze,
                        ),
                        stream_type=StreamType().live_stream,
                    )
                    add_to_queue(chat_id, "Live Stream", livelink, link, "Video", Q)
                    await loser.delete()
                    requester = (
                        f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                    )
                    await m.reply_photo(
                        photo=f"{IMG_2}",
                        caption=f"💡 **[بدء البث]({link}) تم التشغيل.**\n\n💭 **الدردشة:** `{chat_id}`\n💡 **الحالة:** `مشغل طبيعي`\n🎧 **طلب من:** {requester}",
                        reply_markup=keyboard,
                    )
                except Exception as ep:
                    await loser.delete()
                    await m.reply_text(f"🚫 error: `{ep}`")
