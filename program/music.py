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
from pytgcalls.types.input_stream import AudioPiped
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
        "bestaudio",
        f"{link}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if stdout:
        return 1, stdout.decode().split("\n")[0]
    else:
        return 0, stderr.decode()


@Client.on_message(command(["شغل", f"play@{BOT_USERNAME}"]) & other_filters)
async def play(c: Client, m: Message):
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
        return await m.reply_text("انت'مستخدم __مجهول__ !\n\n» لايمكنك استخدام هذا البوت الان .")
    try:
        aing = await c.get_me()
    except Exception as e:
        return await m.reply_text(f"error:\n\n{e}")
    a = await c.get_chat_member(chat_id, aing.id)
    if a.status != "administrator":
        await m.reply_text(
            f"💡 لاتستطيع استخدام البوت,غليك اولا بترقيتي كمشرف هنا **وبعد ذالك امنحني الصلاحيات التالية** لم اعمل ان لم  **تعطيني**:\n\n» ❌ __حذف الرسائل__\n» ❌ __حظر المستخدمين__\n» ❌ __اضافة مستخدمين__\n» ❌ __ادارة المحادثات الصوتية__\n\nبعد   ذالك **سيتم تحديث** البيانات تلقائيا **اجعلني كمشرف الان**"
        )
        return
    if not a.can_manage_voice_chats:
        await m.reply_text(
            "شلون اشغل وانا معندي صلاحية:" + "\n\n» ❌ __ادارة المحادثات الصوتية__"
        )
        return
    if not a.can_delete_messages:
        await m.reply_text(
            "شلون اشغل وانا معندي صلاحية:" + "\n\n» ❌ __حذف الرسائل__"
        )
        return
    if not a.can_invite_users:
        await m.reply_text("شلون اشغل وانا معندي صلاحية:" + "\n\n» ❌ __اضافة مستخدمين__")
        return
    if not a.can_restrict_members:
        await m.reply_text("شلون اشغل وانا معندي صلاحية:" + "\n\n» ❌ __حظر المستخدمين__")
        return
    try:
        ubot = await user.get_me()
        b = await c.get_chat_member(chat_id, ubot.id)
        if b.status == "kicked":
            await m.reply_text(
                f"@{ASSISTANT_NAME} **ياعيني حساب المساعد محظور** {m.chat.title}\n\n» **قم بالغاء حظرة وبعد ذالك ارسل الامر .تحديث وبعد ذالك ارسل الامر .انضم.**"
            )
            return
    except UserNotParticipant:
        if m.chat.username:
            try:
                await user.join_chat(m.chat.username)
            except Exception as e:
                await m.reply_text(f"❌ **لم يستطيع حساب المساعد الانضمام**\n\n**السبب**: `{e}`")
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
                    f"❌ **لم يستطيع حساب المساعد الانضمام**\n\n**السبب**: `{e}`"
                )

    if replied:
        if replied.audio or replied.voice:
            suhu = await replied.reply("📥 **جاري التشغيل...**")
            dl = await replied.download()
            link = replied.link
            if replied.audio:
                if replied.audio.title:
                    songname = replied.audio.title[:70]
                else:
                    if replied.audio.file_name:
                        songname = replied.audio.file_name[:70]
                    else:
                        songname = "Audio"
            elif replied.voice:
                songname = "Voice Note"
            if chat_id in QUEUE:
                pos = add_to_queue(chat_id, songname, dl, link, "Audio", 0)
                await suhu.delete()
                await m.reply_photo(
                    photo=f"{IMG_1}",
                    caption=f"💡 **يالله تم حشغلها وره هاي »** `{pos}`\n\n🏷 **الاسم:** [{songname}]({link})\n💭 **الدردشة:** `{chat_id}`\n🎧 **طلب من:** {m.from_user.mention()}",
                    reply_markup=keyboard,
                )
            else:
             try:
                await call_py.join_group_call(
                    chat_id,
                    AudioPiped(
                        dl,
                    ),
                    stream_type=StreamType().local_stream,
                )
                add_to_queue(chat_id, songname, dl, link, "Audio", 0)
                await suhu.delete()
                requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                await m.reply_photo(
                    photo=f"{IMG_2}",
                    caption=f"💡 **يالله تم شغلتها وانا خادم.**\n\n🏷 **الاسم:** [{songname}]({link})\n💭 **الدردشة:** `{chat_id}`\n💡 **الحاله:** `مشغل طبيعي`\n🎧 **طلب من:** {requester}",
                    reply_markup=keyboard,
                )
             except Exception as e:
                await suhu.delete()
                await m.reply_text(f"🚫 error:\n\n» {e}")
        else:
            if len(m.command) < 2:
                await m.reply(
                    "» ياعيني رد ع ملف **صوتي**او **انطيني شي خلبحث عليه.**"
                )
            else:
                suhu = await m.reply("🔎 **جاري البحث اصبر...**")
                query = m.text.split(None, 1)[1]
                search = ytsearch(query)
                if search == 0:
                    await suhu.edit("❌ **لم يتم العثور على نتائج.**")
                else:
                    songname = search[0]
                    url = search[1]
                    veez, ytlink = await ytdl(url)
                    if veez == 0:
                        await suhu.edit(f"❌ yt-dl issues detected\n\n» `{ytlink}`")
                    else:
                        if chat_id in QUEUE:
                            pos = add_to_queue(
                                chat_id, songname, ytlink, url, "Audio", 0
                            )
                            await suhu.delete()
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
                                    AudioPiped(
                                        ytlink,
                                    ),
                                    stream_type=StreamType().local_stream,
                                )
                                add_to_queue(chat_id, songname, ytlink, url, "Audio", 0)
                                await suhu.delete()
                                requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                                await m.reply_photo(
                                    photo=f"{IMG_2}",
                                    caption=f"💡 **يالله تم شغلتها عيني.**\n\n🏷 **الاسم:** [{songname}]({url})\n💭 **الدردشة:** `{chat_id}`\n💡 **الحاله:** `مشغل طبيعي`\n🎧 **طلب من:** {requester}",
                                    reply_markup=keyboard,
                                )
                            except Exception as ep:
                                await suhu.delete()
                                await m.reply_text(f"🚫 error: `{ep}`")

    else:
        if len(m.command) < 2:
            await m.reply(
                "» ياغبي رد على **ملف صوتي** او **انطيني شي خلبحث علية.**"
            )
        else:
            suhu = await m.reply("🔎 **جاري البحث اصبر...**")
            query = m.text.split(None, 1)[1]
            search = ytsearch(query)
            if search == 0:
                await suhu.edit("❌ **ملكيت شي دعبل.**")
            else:
                songname = search[0]
                url = search[1]
                veez, ytlink = await ytdl(url)
                if veez == 0:
                    await suhu.edit(f"❌ yt-dl issues detected\n\n» `{ytlink}`")
                else:
                    if chat_id in QUEUE:
                        pos = add_to_queue(chat_id, songname, ytlink, url, "Audio", 0)
                        await suhu.delete()
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
                                AudioPiped(
                                    ytlink,
                                ),
                                stream_type=StreamType().local_stream,
                            )
                            add_to_queue(chat_id, songname, ytlink, url, "Audio", 0)
                            await suhu.delete()
                            requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                            await m.reply_photo(
                                photo=f"{IMG_2}",
                                caption=f"💡 **يالله تم شغلتها عيوني.**\n\n🏷 **الاسم:** [{songname}]({url})\n💭 **الدردشة:** `{chat_id}`\n💡 **الحاله:** `مشغل طبيعي`\n🎧 **طلب من:** {requester}",
                                reply_markup=keyboard,
                            )
                        except Exception as ep:
                            await suhu.delete()
                            await m.reply_text(f"🚫 error: `{ep}`")


# stream is used for live streaming only


@Client.on_message(command(["تدفق", f"stream@{BOT_USERNAME}"]) & other_filters)
async def stream(c: Client, m: Message):
    chat_id = m.chat.id
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(text="•تحكم", callback_data="cbmenu"),
                InlineKeyboardButton(text="•اغلاق", callback_data="cls"),
            ]
        ]
    )
    if m.sender_chat:
        return await m.reply_text("انت مستخدم محهول __لايمكنك__ !\n\n» استخدام هذا البوت الان.")
    try:
        aing = await c.get_me()
    except Exception as e:
        return await m.reply_text(f"error:\n\n{e}")
    a = await c.get_chat_member(chat_id, aing.id)
    if a.status != "administrator":
        await m.reply_text(
            f"💡 لاتستطيع استخدامي, عليك بترقيتي كمشرف اولا **وبعد ذالك** امنحني الصلاحيات **اتالية**:\n\n» ❌ __حذف الرسائل__\n» ❌ __حظر المستخدمين__\n» ❌ __اضافة مستخدمين__\n» ❌ _ادارة المحادثات الصوتية__\n\nفقط قم بترقيتي **سيتم** تحديث البيانات **تلقائيا**"
        )
        return
    if not a.can_manage_voice_chats:
        await m.reply_text(
            "شلون اشغل وانا معندي صلاحية:" + "\n\n» ❌ __ادارة المحادثات الصوتية__"
        )
        return
    if not a.can_delete_messages:
        await m.reply_text(
            "شلون اشغل وانا معندي صلاحية:" + "\n\n» ❌ __حذف الرسائل__"
        )
        return
    if not a.can_invite_users:
        await m.reply_text("شلون اشغل وانا معندي صلاحية:" + "\n\n» ❌ __اضاقة مستخدمين__")
        return
    if not a.can_restrict_members:
        await m.reply_text("شلون اشغل وانا معندي صلاحية:" + "\n\n» ❌ __حظر المستخدمين__")
        return
    try:
        ubot = await user.get_me()
        b = await c.get_chat_member(chat_id, ubot.id)
        if b.status == "kicked":
            await m.reply_text(
                f"@{ASSISTANT_NAME} **ياعيني يحلو حساب مساعد محظور** {m.chat.title}\n\n» **قم بالغاء حظره وبعد ذالك ارسل .تحديث وبعد ذالك ارسل .انضم.**"
              )
            return
    except UserNotParticipant:
        if m.chat.username:
            try:
                await user.join_chat(m.chat.username)
            except Exception as e:
                await m.reply_text(f"❌ **لم يستطيع حساب المساعد بلالانضمام**\n\n**السبب**: `{e}`")
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
                    f"❌ **لم يستطيع حساب المساعد بالانضام**\n\n**السبب**: `{e}`"
                )

    if len(m.command) < 2:
        await m.reply("» give me a live-link/m3u8 url/youtube link to stream.")
    else:
        link = m.text.split(None, 1)[1]
        suhu = await m.reply("🔄 **جاري التحميل...**")

        regex = r"^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+"
        match = re.match(regex, link)
        if match:
            veez, livelink = await ytdl(link)
        else:
            livelink = link
            veez = 1

        if veez == 0:
            await suhu.edit(f"❌ yt-dl issues detected\n\n» `{ytlink}`")
        else:
            if chat_id in QUEUE:
                pos = add_to_queue(chat_id, "راديو", livelink, link, "Audio", 0)
                await suhu.delete()
                requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                await m.reply_photo(
                    photo=f"{IMG_1}",
                    caption=f"💡 **يالله تم حشغلها وره هاي »** `{pos}`\n\n💭 **الدردشة:** `{chat_id}`\n🎧 **طلب من:** {requester}",
                    reply_markup=keyboard,
                )
            else:
                try:
                    await call_py.join_group_call(
                        chat_id,
                        AudioPiped(
                            livelink,
                        ),
                        stream_type=StreamType().live_stream,
                    )
                    add_to_queue(chat_id, "راديو", livelink, link, "Audio", 0)
                    await suhu.delete()
                    requester = (
                        f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                    )
                    await m.reply_photo(
                        photo=f"{IMG_2}",
                        caption=f"💡 **[بدء البث]({link}) تم التشغيل.**\n\n💭 **الدردشة:** `{chat_id}`\n💡 **الحالة:** `مشغل طبيعي`\n🎧 **طلب من:** {requester}",
                        reply_markup=keyboard,
                    )
                except Exception as ep:
                    await suhu.delete()
                    await m.reply_text(f"🚫 error: `{ep}`")
