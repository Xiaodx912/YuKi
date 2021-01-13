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
        if self.Client.state == self.Client.OFFLINE:
            if time.time()>self.Client.login_time+self.config["login_cd"]:
                await self.Client.login(self.uid, self.access_key)
            else:
                logger.debug("Client loging cd")
        while self.Client.state == self.Client.LOGGING:
            logger.info('another instance in logging, do_login wait 2s')
            asyncio.sleep(2)

    async def get_profile(self, target_uid:int):
        logger.debug(f'get_profile:{target_uid}')
        await self.do_login()
        if self.Client.state == self.Client.OFFLINE:
            logger.error("BCRClient not ready,get profile fail")
            return {}
        profile = await self.Client.Callapi('profile/get_profile',{'target_viewer_id':target_uid})
        #logger.debug(profile)
        rec={}
        try:
            rec['time']=time.time()
            rec['name']=profile['user_info']['user_name']
            rec['arena_rank']=profile['user_info']['arena_rank']
            rec['grand_arena_rank']=profile['user_info']['grand_arena_rank']
        except:
            #logger.debug(profile)
            return {}
        return rec


    async def add_uid(self, target_uid:int, qqid:int, group_id:int):
        logger.debug(f"add_uid {target_uid}")
        rec = await self.get_profile(int(target_uid))
        if rec == {}:
            logger.error("empty profile, add fail")
            return "empty profile, add fail"
        if str(target_uid) in list(self.db.keys()):
            logger.error("uid item exist")
            return "uid item exist"
        data={}
        data['rec']=rec
        data['qqid']=qqid
        data['group']=group_id
        self.db[target_uid]=data
        return "bind fin"

    async def remove_uid(self, target_uid:int):
        if str(target_uid) not in list(self.db.keys()):
            logger.error("uid item not exist")
            return
        self.db.pop(target_uid)
    
    async def remind_gen(self,old_rec,new_rec,uid):
        remind_list=[]
        Tdelta=new_rec['time']-old_rec['time']
        for arena_type in ['arena_rank','grand_arena_rank']
            prev,now = old_rec[arena_type],new_rec[arena_type]
            if rec > prev:
                remind_list.append({'uid':uid,'name':new_rec['name'],'type':arena_type,'prev':prev,'now':now,'T':Tdelta,
                                    'isElevator':prev < search_max(now) and Tdelta <= self.config['elevator_timer']})
        return remind_list

    async def update_profile(self, target_uid:int):
        remind_list=[]
        rec = await self.get_profile(target_uid)
        if rec == {}:
            logger.error("empty profile, update fail")
            return remind_list
        data=self.db[target_uid]
        prev=data['rec']
        remind_list.extend(await self.remind_gen(prev,rec,target_uid))
        data['rec']=rec
        self.db[target_uid]=data
        return remind_list

    async def update_all(self):
        remind_list=[]
        for uid in self.db.keys():
            remind_list.extend(await self.update_profile(int(uid)))
        return remind_list

    def bind_status(self,target_qqid:int):
        bind_list=[]
        for item in self.db.items():
            if item[1]['qqid']==target_qqid:
                bind_list.append(item)
        return bind_list

#from ArenaMonitor import *
