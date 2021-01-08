from os import path
import asyncio
import datetime
import requests
import ast
import re
import hashlib
import base64

import hoshino
import asyncio
from .ArenaMonitor import ArenaMonitor

sv = hoshino.Service('YuKi', visible=False)

yuki=ArenaMonitor(1160936629251, '267364644', '771c02865f3ab18e29381d0de5aac04e_sh')
asyncio.run(yuki.do_login())

@sv.scheduled_job('cron', minute='*/1')
async def schedule_update_all_profile():
    await yuki.update_all()

@sv.on_fullmatch('YuKi_update')
async def manual_update_all_profile(bot, ev):
    await yuki.update_all()
    await bot.send(ev, "YuKi updated {} users' profile".format(len(list(yuki.db.keys()))))

@sv.on_prefix('YuKi_add')
async def add_watch_list(bot, ev):
    args = ev.message.extract_plain_text().split()
    try:
        uid = args[0]
        qqid = args[1]
    except:
        await bot.send(ev,'YuKi_add <uid> <qqid>')
        return
    if len(str(uid)) != 13:
        await bot.send(ev,'uid length not match')
        return
    await yuki.add_uid(uid,qqid)
    await bot.send(ev, "add fin")

