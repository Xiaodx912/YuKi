from os import path
import asyncio
import datetime
import hoshino
from .ArenaMonitor import ArenaMonitor, get_config

sv = hoshino.Service('YuKi', visible=False)
logger = hoshino.log.new_logger('YuKi')

from apscheduler.triggers.date import DateTrigger
from nonebot import scheduler

config = get_config()
yuki=ArenaMonitor(config['_viewerid'], config['_uid'], config['_access_key'])
scheduler.add_job(
        func=yuki.do_login,
        trigger=DateTrigger(run_date=datetime.datetime.now() + datetime.timedelta(seconds=10)),
        args=(),
        misfire_grace_time=1)

@sv.scheduled_job('interval', seconds=config['refresh_cd'])
async def scheduled_update():
    bot=hoshino.get_bot()
    mention_info=await yuki.update_all()
    logger.debug(mention_info)
    for info in mention_info:
        if config['private_mode']:
            await bot.send_msg(user_id=yuki.db[info['uid']]['qqid'], message=info['str'],auto_escape=True)
        else:
            await bot.send_msg(group_id=yuki.db[info['uid']]['group'], message=info['str'])


@sv.on_fullmatch('YuKi_update')
async def manual_update(bot, ev):
    if not hoshino.priv.check_priv(ev, hoshino.priv.SUPERUSER):
        await bot.send(ev,'admin only')
    mention_info=await yuki.update_all()
    await bot.send(ev, f"YuKi updated {len(list(yuki.db.keys()))} users' profile, generate {len(mention_info)} reminds")
    for info in mention_info:
        if config['private_mode']:
            await bot.send_msg(user_id=yuki.db[info['uid']]['qqid'], message=info['str'],auto_escape=True)
        else:
            await bot.send_msg(group_id=yuki.db[info['uid']]['group'], message=info['str'])


@sv.on_prefix('YuKi_add')
async def add_watch_list(bot, ev):
    if not hoshino.priv.check_priv(ev, hoshino.priv.SUPERUSER):
        await bot.send(ev,'admin only')
    args = ev.message.extract_plain_text().split()
    try:
        uid = args[0]
        qqid = args[1]
        group = args[2]
    except:
        await bot.send(ev,'YuKi_add <uid> <qqid> <group>')
        return
    if len(str(uid)) != 13:
        await bot.send(ev,'uid length not match')
        return
    if ev['user_id']!=qqid and not hoshino.priv.check_priv(ev ,hoshino.priv.ADMIN):
        await bot.send(ev, "Only admin can add to other's qq")
        return
    await yuki.add_uid(uid,qqid,group)
    await bot.send(ev, "add fin")

@sv.on_prefix('YuKi_bind')
async def bind_self_uid(bot,ev):
    args = ev.message.extract_plain_text().split()
    try:
        uid = args[0]
        qqid = ev.user_id
        group = ev.group_id
    except:
        await bot.send(ev,'YuKi_bind <uid>(in group only)')
        return
    if len(str(uid)) != 13:
        await bot.send(ev,'uid length not match')
        return
    await yuki.add_uid(uid,qqid,group)
    await bot.send(ev, "bind fin")


