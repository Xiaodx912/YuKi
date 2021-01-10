import requests
import ast
import hashlib
import base64
import random
import os
import time
import asyncio
from PCRClient import PCRClient
import logging
from sqlitedict import SqliteDict
import json

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
                logging.debug("Client loging cd")

    async def get_profile(self, target_uid:int):
        await self.do_login()
        if not self.Client.ready:
            logging.error("BCRClient not ready,get profile fail")
            return {}
        profile = await self.Client.Callapi('profile/get_profile',{'target_viewer_id':target_uid})
        rec={}
        rec['time']=time.time()
        rec['arena_rank']=profile['user_info']['arena_rank']
        rec['grand_arena_rank']=profile['user_info']['grand_arena_rank']
        return rec


    async def add_uid(self, target_uid:int, qqid:int):
        rec = await self.get_profile(target_uid)
        if rec == {}:
            logging.error("empty profile, add fail")
            return
        if str(target_uid) in list(self.db.keys()):
            logging.error("uid item exist")
            return
        data={}
        data['rec']=rec
        data['qqid']=qqid
        self.db[target_uid]=data

    async def remove_uid(self, target_uid:int):
        if str(target_uid) not in list(self.db.keys()):
            logging.error("uid item not exist")
            return
        self.db.pop(target_uid)

        
    async def mention_test(self,qqid:int,type:str,prev:int,now:int,delta):
        info_str=f"{qqid}'s {type} decrease from {prev} to {now}"
        if prev < search_max(now) and delta <= self.config['elevator_timer']:
            info_str += f"in {int(delta)}S\nCurrent search max is {search_max(now)}, elevator detected"
        print(info_str)
        return {'qqid':qqid, 'type':type, 'prev':prev, 'now':now, 'str':info_str}
        
    async def update_profile(self, target_uid:int, mention_func=mention_test):
        mention_info=[]
        rec = await self.get_profile(target_uid)
        data=self.db[target_uid]
        prev=data['rec']
        delta=rec['time']-prev['time']
        if rec['arena_rank'] > prev['arena_rank']:
            mention_info.append(await self.mention_func(data['qqid'],'jjc',prev['arena_rank'],rec['arena_rank']),delta)
        if rec['grand_arena_rank'] > prev['grand_arena_rank']:
            mention_info.append(await self.mention_func(data['qqid'],'pjjc',prev['grand_arena_rank'],rec['grand_arena_rank']),delta)
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
                bind_list.append((uid,data))
        return bind_list

def aaa():
    a=ArenaMonitor(1160936629251, '267364644', '771c02865f3ab18e29381d0de5aac04e_sh')
    asyncio.run(a.do_login())
    asyncio.run(a.update_all())
    return a
#from ArenaMonitor import *

