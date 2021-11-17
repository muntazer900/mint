import asyncio
from config import BOT_USERNAME, SUDO_USERS
from driver.decorators import authorized_users_only, sudo_users_only, errors
from driver.filters import command, other_filters
from driver.veez import user as USER
from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant


@Client.on_message(
    command(["انضم", f"userbotjoin@{BOT_USERNAME}"]) & ~filters.private & ~filters.bot
)
@authorized_users_only
@errors
async def join_group(client, message):
    chid = message.chat.id
    try:
        invitelink = await client.export_chat_invite_link(chid)
    except BaseException:
        await message.reply_text(
            "• **يخي لا استطيع دعوة حساب المساعد م عندي صلاحية:**\n\n» ❌ __اضافة مستخدمين__",
        )
        return

    try:
        user = await USER.get_me()
    except BaseException:
        user.first_name = "music assistant"

    try:
        await USER.join_chat(invitelink)
    except UserAlreadyParticipant:
        pass
    except Exception as e:
        print(e)
        await message.reply_text(
            f"🛑 م كدر حساب المساعد ينضم 🛑 \n\n**بسبب كثرة الطلبات على الانضمام في المجموعات**"
            "\n\n**اكتب .انضم او قم باضافتة يدويا**",
        )
        return
    await message.reply_text(
        f"✅ **تم ياعيني انضم حساب المساعد**",
    )


@Client.on_message(command(["اطلع",
                            f"leave@{BOT_USERNAME}"]) & filters.group & ~filters.edited)
@authorized_users_only
async def leave_one(client, message):
    try:
        await USER.send_message(message.chat.id, "✅ هوه مو صوجكم صوجي اني اجيت باي")
        await USER.leave_chat(message.chat.id)
    except BaseException:
        await message.reply_text(
            "❌ **ميكدر حساب المساعد يغادر.**\n\n**» اطرده بنفسك ولتصير دودكي**"
        )

        return


@Client.on_message(command(["مغادرة كل المجموعات", f"leaveall@{BOT_USERNAME}"]))
@sudo_users_only
async def leave_all(client, message):
    if message.from_user.id not in SUDO_USERS:
        return

    left = 0
    failed = 0
    lol = await message.reply("🔄 **اهلا مطوري** جاري مغادرة كل المجموعات !")
    async for dialog in USER.iter_dialogs():
        try:
            await USER.leave_chat(dialog.chat.id)
            left += 1
            await lol.edit(
                f"عدد المجموعات التي غادرت منها...\n\nLeft: {left} chats.\nFailed: {failed} chats."
            )
        except BaseException:
            failed += 1
            await lol.edit(
                f"تم مغادرة جميع المجموعات...\n\nLeft: {left} chats.\nFailed: {failed} chats."
            )
        await asyncio.sleep(0.7)
    await client.send_message(
        message.chat.id, f"✅ تم مغادرة حساب المساعد من: {left} chats.\n❌ Failed in: {failed} chats."
    )
