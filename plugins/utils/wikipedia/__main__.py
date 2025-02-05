""" wikipedia search """

# Copyright (C) 2020-2022 by UsergeTeam@Github, < https://github.com/UsergeTeam >.
#
# This file is part of < https://github.com/UsergeTeam/Userge > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/UsergeTeam/Userge/blob/master/LICENSE >
#
# All rights reserved.

import wikipedia

from userge import userge, Message
from pyrogram.types import LinkPreviewOptions

@userge.on_cmd("wiki", about={
    'header': "do a Wikipedia search",
    'flags': {'-l': "limit the number of returned results (defaults to 5)"},
    'usage': "{tr}wiki [flags] [query | reply to msg]",
    'examples': "{tr}wiki -l5 userge"})
async def wiki_pedia(message: Message):
    await message.edit("Processing ...")
    query = message.filtered_input_str
    flags = message.flags
    limit = int(flags.get('-l', 5))
    if message.reply_to_message:
        query = message.reply_to_message.text
    if not query:
        await message.err(text="Give a query or reply to a message to wikipedia!")
        return
    try:
        wikipedia.set_lang("en")
        results = wikipedia.search(query)
    except Exception as e:
        await message.err(e)
        return
    output = ""
    for i, s in enumerate(results, start=1):
        page = wikipedia.page(s)
        url = page.url
        output += f"🌏 [{s}]({url})\n"
        if i == limit:
            break
    output = f"**Wikipedia Search:**\n`{query}`\n\n**Results:**\n{output}"
    await message.edit_or_send_as_file(text=output, caption=query,
                                       link_preview_options=LinkPreviewOptions(is_disabled=True))
