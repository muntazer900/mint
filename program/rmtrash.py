# Copyright (C) 2021 By VeezMusicProject

import os
from pyrogram import Client, filters
from pyrogram.types import Message
from driver.filters import command, other_filters
from driver.decorators import sudo_users_only, errors

downloads = os.path.realpath("program/downloads")
raw = os.path.realpath(".")

@Client.on_message(command(["امسح", "احذف"]) & ~filters.edited)
@errors
@sudo_users_only
async def clear_downloads(_, message: Message):
    ls_dir = os.listdir(downloads)
    if ls_dir:
        for file in os.listdir(downloads):
            os.remove(os.path.join(downloads, file))
        await message.reply_text("✅ **حذف جميع الملفات التي تم تنزيلها**")
    else:
        await message.reply_text("❌ **لم يتم تنزيل أي ملفات**")

        
@Client.on_message(command(["ملح", "عسل"]) & ~filters.edited)
@errors
@sudo_users_only
async def clear_raw(_, message: Message):
    ls_dir = os.listdir(raw)
    if ls_dir:
        for file in os.listdir(raw):
            if file.endswith('.raw'):
                os.remove(os.path.join(raw, file))
        await message.reply_text("✅ **حذف جميع الملفات الخام**")
    else:
        await message.reply_text("❌ **لم يتم العثور على ملفات خام**")


@Client.on_message(command(["نظف"]) & ~filters.edited)
@errors
@sudo_users_only
async def cleanup(_, message: Message):
    pth = os.path.realpath(".")
    ls_dir = os.listdir(pth)
    if ls_dir:
        for dta in os.listdir(pth):
            os.system("rm -rf *.raw *.jpg")
        await message.reply_text("✅ **تم التنظيف**")
    else:
        await message.reply_text("✅ **منظفة بالفعل**")
