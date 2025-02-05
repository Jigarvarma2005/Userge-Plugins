""" get snapshot of website """

# Copyright (C) 2020-2022 by UsergeTeam@Github, < https://github.com/UsergeTeam >.
#
# This file is part of < https://github.com/UsergeTeam/Userge > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/UsergeTeam/Userge/blob/master/LICENSE >
#
# All rights reserved.

import asyncio
import os
from re import match

import aiofiles
from fake_headers import Headers
from selenium import webdriver
from pyrogram.types import ReplyParameters
from userge import userge, Message, config
from .. import webss


@userge.on_cmd("webss", about={'header': "Get snapshot of a website"})
async def _webss(message: Message):
    if webss.GOOGLE_CHROME_BIN is None:
        await message.edit("`need to install Google Chrome. Module Stopping`", del_in=5)
        return
    link_match = match(r'\bhttps?://.*\.\S+', message.input_str)
    if not link_match:
        await message.err("I need a valid link to take screenshots from.")
        return
    link = link_match.group()
    await message.edit("`Processing ...`")
    chrome_options = webdriver.ChromeOptions()
    header = Headers(headers=False).generate()
    chrome_options.binary_location = webss.GOOGLE_CHROME_BIN
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument("--test-type")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument(f"user-agent={header['User-Agent']}")
    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.get(link)
    height = driver.execute_script(
        "return Math.max(document.body.scrollHeight, document.body.offsetHeight, "
        "document.documentElement.clientHeight, document.documentElement.scrollHeight, "
        "document.documentElement.offsetHeight);")
    width = driver.execute_script(
        "return Math.max(document.body.scrollWidth, document.body.offsetWidth, "
        "document.documentElement.clientWidth, document.documentElement.scrollWidth, "
        "document.documentElement.offsetWidth);")
    driver.set_window_size(width + 125, height + 125)
    wait_for = height / 1000
    await message.edit(f"`Generating screenshot of the page...`"
                       f"\n`Height of page = {height}px`"
                       f"\n`Width of page = {width}px`"
                       f"\n`Waiting ({int(wait_for)}s) for the page to load.`")
    await asyncio.sleep(int(wait_for))
    im_png = driver.get_screenshot_as_png()
    driver.close()
    message_id = message.id
    if message.reply_to_message:
        message_id = message.reply_to_message.id
    file_path = os.path.join(config.Dynamic.DOWN_PATH, "webss.png")
    async with aiofiles.open(file_path, 'wb') as out_file:
        await out_file.write(im_png)
    await asyncio.gather(
        message.delete(),
        message.client.send_document(chat_id=message.chat.id,
                                     document=file_path,
                                     caption=link,
                                     reply_parameters=ReplyParameters(message_id=message_id))
    )
    os.remove(file_path)
    driver.quit()
