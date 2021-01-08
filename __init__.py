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
    len=len(list(yuki.db.keys()))
    await bot.send(ev, "YuKi updated {len} users' profile")

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


@on_command('开启推送档线', only_to_me = False, permission = perm.SUPERUSER)
async def set_open_score_line(session):
    match = re.match(r'^(\d+):(\d+)', session.current_arg)
    if not match:
        return
    hour = int(match.group(1))
    minute = int(match.group(2))
    global Push_Score_Lines
    if Push_Score_Lines != None:
        scheduler.remove_job(Push_Score_Lines)
        Push_Score_Lines = None
    scheduler.add_job(push_score_line_scheduled, 'cron', hour = hour, minute = minute, id = 'score_lines_open')
    Push_Score_Lines = 'score_lines_open'
    await session.send(message.MessageSegment.text('每日{}:{}会自动推送当前档线'.format(str(hour).zfill(2), str(minute).zfill(2))))
