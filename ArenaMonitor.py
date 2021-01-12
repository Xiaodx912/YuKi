import requests
import os
import time
import asyncio
from .PCRClient import *
from sqlitedict import SqliteDict
import json

try:
    from hoshino import log
    logger = log.new_logger('YuKi')
except:
    import logging
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('YuKi')
    logger.setLevel(logging.DEBUG)

def get_path(*paths):
    return os.path.join(os.path.dirname(__file__), *paths)

def get_config():
    file = open(os.path.join(os.path.dirname(__file__), "config.json"), 'r', encoding="utf-8")
    return json.load(file)

def init_db(db_dir, db_name='YuKi.sqlite'):
    return SqliteDict(get_path(db_dir, db_name),
                      encode=json.dumps,
                      decode=json.loads,
                      autocommit=True)

def search_max(now:int):
    if now<=69:
        return max(now-10,1)
    return int(now*0.85)

class ArenaMonitor:
    def __init__(self, viewer_id, uid, access_key):
        self.config = get_config()
        self.db = init_db(self.config['db_dir'])
        self.uid = uid
        self.access_key = access_key

        self.Client = PCRClient(viewer_id,self.config['verify'])

    async def do_login(self):
        if not self.Client.ready:
            if time.time()>self.Client.login_time+self.config["login_cd"]:
                await self.Client.login(self.uid, self.access_key)
            else:
                logger.debug("Client loging cd")

    async def get_profile(self, target_uid:int):
        await self.do_login()
        if not self.Client.ready:
            logger.error("BCRClient not ready,get profile fail")
            return {}
        profile = await self.Client.Callapi('profile/get_profile',{'target_viewer_id':target_uid})
        logger.debug(profile)
        rec={}
        try:
            rec['time']=time.time()
            rec['name']=profile['user_info']['user_name']
            rec['arena_rank']=profile['user_info']['arena_rank']
            rec['grand_arena_rank']=profile['user_info']['grand_arena_rank']
        except:
            return {}
        return rec


    async def add_uid(self, target_uid:int, qqid:int, group_id:int):
        rec = await self.get_profile(target_uid)
        if rec == {}:
            logger.error("empty profile, add fail")
            return
        if str(target_uid) in list(self.db.keys()):
            logger.error("uid item exist")
            return
        data={}
        data['rec']=rec
        data['qqid']=qqid
        data['group']=group_id
        self.db[target_uid]=data

    async def remove_uid(self, target_uid:int):
        if str(target_uid) not in list(self.db.keys()):
            logger.error("uid item not exist")
            return
        self.db.pop(target_uid)

        
    async def mention_test(self,uid:int,type:str,prev:int,now:int,delta):
        info_str=f"===Group {self.db[uid]['group']}===\n"+f"[CQ:at,qq={self.db[uid]['qqid']}] {self.db[uid]['rec']['name']}'s {type} {prev}->{now}"
        if prev < search_max(now) and delta <= self.config['elevator_timer']:
            info_str += f" in {int(delta)}S\n"+f"Current search max is {search_max(now)}, elevator detected"
        return {'uid':uid, 'type':type, 'prev':prev, 'now':now, 'str':info_str}
        
    async def update_profile(self, target_uid:int, mention_func=mention_test):
        mention_info=[]
        rec = await self.get_profile(target_uid)
        if rec == {}:
            logger.error("empty profile, update fail")
            return mention_info
        data=self.db[target_uid]
        prev=data['rec']
        delta=rec['time']-prev['time']
        if rec['arena_rank'] > prev['arena_rank']:
            mention_info.append(await mention_func(self,target_uid,'jjc',prev['arena_rank'],rec['arena_rank'],delta))
        if rec['grand_arena_rank'] > prev['grand_arena_rank']:
            mention_info.append(await mention_func(self,target_uid,'pjjc',prev['grand_arena_rank'],rec['grand_arena_rank'],delta))
        data['rec']=rec
        self.db[target_uid]=data
        return mention_info

    async def update_all(self):
        mention_info=[]
        for uid in self.db.keys():
            mention_info.extend(await self.update_profile(int(uid)))
        return mention_info

    def bind_status(self,target_qqid:int):
        bind_list=[]
        for item in self.db.items():
            if item[1]['qqid']==target_qqid:
                bind_list.append(item)
        return bind_list

#from ArenaMonitor import *
