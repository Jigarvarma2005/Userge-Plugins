""" Mentions alerter Plugin """

# Copyright (C) 2020-2022 by UsergeTeam@Github, < https://github.com/UsergeTeam >.
#
# This file is part of < https://github.com/UsergeTeam/Userge > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/UsergeTeam/Userge/blob/master/LICENSE >
#
# All rights reserved.

import os
from pyrogram.errors import PeerIdInvalid, BadRequest, UserIsBlocked
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LinkPreviewOptions
from pyrogram import enums

from userge import userge, Message, config, filters, get_collection

SAVED_SETTINGS = get_collection("CONFIGS")
TOGGLE = False


@userge.on_start
async def _init():
    global TOGGLE  # pylint: disable=global-statement
    data = await SAVED_SETTINGS.find_one({"_id": "MENTION_TOGGLE"})
    if data:
        TOGGLE = bool(data["data"])


@userge.on_cmd(
    "mentions",
    about="Toggles Mentions, "
          "if enabled Bot will send Message if anyone mention you."
)
async def toggle_mentions(msg: Message):
    """ toggle mentions """
    global TOGGLE  # pylint: disable=global-statement
    TOGGLE = not TOGGLE
    await SAVED_SETTINGS.update_one(
        {"_id": "MENTION_TOGGLE"}, {"$set": {"data": TOGGLE}}, upsert=True
    )
    await msg.edit(f"Mentions Alerter **{'enabled' if TOGGLE else 'disabled'}** Successfully.")


@userge.on_filters(
    ~filters.me & ~filters.bot & ~filters.service
    & (filters.mentioned | filters.private), group=1, allow_via_bot=False)
async def handle_mentions(msg: Message, is_retry=False):
    # sourcery skip: low-code-quality

    if TOGGLE is False:
        return

    if not msg.from_user or msg.from_user.is_verified:
        return

    if msg.chat.type == enums.ChatType.PRIVATE:
        is_private = True
        link = f"tg://openmessage?user_id={msg.chat.id}&message_id={msg.id}"
        text = f"{msg.from_user.mention} 💻 sent you a **Private message.**"
    else:
        is_private = False
        if msg.chat.type == enums.ChatType.GROUP:
            link = f"tg://openmessage?chat_id={str(msg.chat.id).strip('-')}&message_id={msg.id}"
        else:
            link = msg.link
        text = f"{msg.from_user.mention} 💻 tagged you in **{msg.chat.title}.**"
    text += "\n\n**Message:**" if userge.has_bot else f"\n\n[Message]({link}):"
    if msg.text:
        text += f"\n`{msg.text}`"
    buttons = [[InlineKeyboardButton(text="📃 Message Link", url=link)]]
    dl_loc = None
    client = userge.bot if userge.has_bot else userge
    if not msg.text:
        if is_private:
            chat_id = config.LOG_CHANNEL_ID
            media_client = userge
        else:
            media_client = client
            chat_id = userge.id if userge.has_bot else config.LOG_CHANNEL_ID
    try:
        if not msg.text:
            try:
                media = msg.photo or msg.video or None
                if media and media.ttl_seconds:
                    dl_loc = await msg.download(config.Dynamic.DOWN_PATH)
                    if isinstance(dl_loc, str):
                        if msg.media.value == "photo":
                            sentMedia = await media_client.send_photo(
                                chat_id,
                                dl_loc
                            )
                        elif msg.media.value == "video":
                            sentMedia = await media_client.send_video(
                                chat_id,
                                dl_loc
                            )
                        else:
                            sentMedia = await media_client.send_document(
                                chat_id,
                                dl_loc
                            )
                else:
                    sentMedia = await media_client.copy_message(
                        chat_id,
                        msg.chat.id,
                        msg.id
                    )
            except (PeerIdInvalid, BadRequest):
                sentMedia = await userge.copy_message(
                    config.LOG_CHANNEL_ID,
                    msg.chat.id,
                    msg.id
                )
            buttons.append([InlineKeyboardButton(text="📃 Media Link", url=sentMedia.link)])
        await client.send_message(
            chat_id=userge.id if userge.has_bot else config.LOG_CHANNEL_ID,
            text=text,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except (PeerIdInvalid, UserIsBlocked) as e:
        if not userge.dual_mode or is_retry:
            raise
        if isinstance(e, UserIsBlocked):
            await userge.unblock_user(userge.bot.id)
        await userge.send_message(userge.bot.id, "/start")
        await handle_mentions(msg, True)
    finally:
        if dl_loc and os.path.exists(dl_loc):
            os.remove(dl_loc)
