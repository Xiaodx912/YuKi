from os import path
import asyncio
import datetime
import hoshino
from .ArenaMonitor import ArenaMonitor, get_config, search_max

sv = hoshino.Service('YuKi', visible=False)
logger = hoshino.log.new_logger('YuKi')

from apscheduler.triggers.date import DateTrigger
from nonebot import scheduler

remind_msg="{name}'s {type} {prev}->{now}"
elevator_msg=" ({diff})in {T}S\nCurrent search limit is {max}. Elevator detected."
def remind2str(remind:dict):
    msg = remind_msg.format(**remind)
    if remind['isElevator']:
        msg += elevator_msg.format(**remind,diff=remind['now']-remind['prev'],max=search_max(remind['now']))
    return msg

config = get_config()
yuki=ArenaMonitor(config['_viewerid'], config['_uid'], config['_access_key'])
scheduler.add_job(
        func=yuki.do_login,
        trigger=DateTrigger(run_date=datetime.datetime.now() + datetime.timedelta(seconds=5)),
        args=(),
        misfire_grace_time=1)


@sv.scheduled_job('interval', seconds=config['refresh_cd'])
async def scheduled_update():
    bot=hoshino.get_bot()
    remind_list=await yuki.update_all()
    logger.debug(remind_list)
    if yuki.Client.state == yuki.Client.RISK:
        try:
            SEND
        except:
            bot.send_msg(user_id=1020080972, message=str(yuki.Client.sdk_login),auto_escape=True)
            SEND=True
    for remind in remind_list:
        msg = remind2str(remind)
        if config['private_mode']:
            await bot.send_msg(user_id=yuki.db[remind['uid']]['qqid'], message=msg,auto_escape=True)
        else:
            cqat=f"[CQ:at,qq={yuki.db[remind['uid']]['qqid']}]\n"
            await bot.send_msg(group_id=yuki.db[remind['uid']]['group'], message=cqat+msg)


@sv.on_fullmatch('YuKi_update')
async def manual_update(bot, ev):
    if not hoshino.priv.check_priv(ev, hoshino.priv.SUPERUSER):
        await bot.send(ev,'admin only')
    remind_list=await yuki.update_all()
    await bot.send(ev, f"YuKi updated {len(list(yuki.db.keys()))} users' profile, generate {len(remind_list)} reminds")
    for remind in remind_list:
        msg = remind2str(remind)
        if config['private_mode']:
            await bot.send_msg(user_id=yuki.db[remind['uid']]['qqid'], message=msg,auto_escape=True)
        else:
            cqat=f"[CQ:at,qq={yuki.db[remind['uid']]['qqid']}]\n"
            await bot.send_msg(group_id=yuki.db[remind['uid']]['group'], message=cqat+msg)


@sv.on_prefix('YuKi_add')
async def add_watch_list(bot, ev):
    if not hoshino.priv.check_priv(ev, hoshino.priv.SUPERUSER):
        await bot.send(ev,'admin only')
        return
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
    await bot.send(ev, await yuki.add_uid(uid,qqid,group))

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
    bind_result = await yuki.add_uid(uid,qqid,group)
    if bind_result == "bind fin":
        bind_result += "\n请主动向bot发送任意内容初始化私聊"
    await bot.send(ev, bind_result)

@sv.on_fullmatch('YuKi_list')
async def list_bind_status(bot,ev):
    bind_list=yuki.bind_status(ev.user_id)
    msg=f"[CQ:at,qq={ev.user_id}]Find {len(bind_list)} records bind to your QQ"
    for item in bind_list:
        logger.debug(item)
        msg+=f"\nNickname:{item[1]['rec']['name']}  UID:{item[0]}"
    await bot.send(ev,msg)

@sv.on_prefix('YuKi_unbind')
async def unbind_self_uid(bot,ev):
    args = ev.message.extract_plain_text().split()
    bind_list=yuki.bind_status(ev.user_id)
    if len(bind_list) == 0:
        await bot.send(ev,"No bind record found")
        return
    if len(args) == 0 and len(bind_list) > 1:
        await bot.send(ev,"Please specific uid to unbind")
        return
    if len(args) == 0:
        uid=bind_list[0][0]
    else:
        uid=args[0]
    if str(uid) not in list(yuki.db.keys()):
        await bot.send(ev,"UID notfound in db")
        return
    if yuki.db[uid]['qqid'] != ev.user_id and not hoshino.priv.check_priv(ev, hoshino.priv.SUPERUSER):
        await bot.send(ev,"Can't unbind others record")
        return
    await yuki.remove_uid(int(uid))
    await bot.send(ev,"Unbind fin")

@sv.on_prefix('YuKi_query')
async def get_specific_profile(bot,ev):
    args = ev.message.extract_plain_text().split()
    if not hoshino.priv.check_priv(ev, hoshino.priv.SUPERUSER):
        await bot.send(ev,'admin only')
        return
    try:
        uid=args[0]
    except:
        await bot.send(ev,'YuKi_query <uid>')
        return
    if len(str(uid)) != 13:
        await bot.send(ev,'uid length not match')
        return
    profile="Result:\n"+str(await yuki.get_profile(int(uid)))
    await bot.send(ev,profile)

@sv.on_fullmatch('YuKi_help')
async def send_help(bot,ev):
    help="""普通指令：
“YuKi_bind UID” ：绑定UID到你的QQ
“YuKi_list” ：列出你的QQ上绑定的UID
“YuKi_unbind UID” ：解绑本QQ绑定的UID，若仅有一条绑定记录可以不填UID

管理指令：
“YuKi_update” ：强制更新所有记录
“YuKi_add UID QQ GROUP” ：添加一条绑定记录
“YuKi_unbind UID” ：解绑任意UID
“YuKi_query UID” ：查询UID的个人信息"""
    await bot.send(ev,help)