from os import path
import asyncio
import datetime

import hoshino
import asyncio
from .ArenaMonitor import ArenaMonitor, get_config

sv = hoshino.Service('YuKi', visible=False)

config = get_config()
yuki=ArenaMonitor(config['_viewerid'], config['_uid'], config['_access_key'])
asyncio.run(yuki.do_login())

@sv.scheduled_job('interval', seconds=config['refresh_cd'])
async def scheduled_update():
    mention_info=await yuki.update_all()
    for info in mention_info:
        await hoshino.get_bot().send_msg(user_id=info['qqid'], message=info['str'])


@sv.on_fullmatch('YuKi_update', permission=SUPERUSER)
async def manual_update(bot, ev):
    mention_info=await yuki.update_all()
    await bot.send(ev, f"YuKi updated {len(list(yuki.db.keys()))} users' profile, generate {len(mention_info)} reminds")
    for info in mention_info:
        await hoshino.get_bot().send_msg(user_id=info['qqid'], message=info['str'])


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
    if ev['user_id']!=qqid and not hoshino.priv.check_priv(ev ,hoshino.priv.ADMIN):
        await bot.send(ev, "Only admin can bind to other's qq")
        return
    await yuki.add_uid(uid,qqid)
    await bot.send(ev, "add fin")

#todo
#switch to send(bot, ev, message, ensure_private=True)

