import requests
import ast
import hashlib
import base64
import random
import os
import time
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

class ArenaMonitor:
    def __init__(self, viewer_id, uid, access_key):
        self.config = get_config()
        self.db = init_db(self.config['db_dir'])
        self.uid = uid
        self.access_key = access_key

        self.Client = PCRClient(viewer_id)
        self.Client.login(self.uid, self.access_key)

    def do_login():
        if not self.Client.ready:
            if time.time()>self.Client.login_time+self.config["login_cd"]:
                self.Client.login(self.uid, self.access_key)
            else:
                logging.debug("Client loging cd")

    def get_profile(self, target_id):
        self.do_login()
        if not self.Client.ready:
            logging.error("BCRClient not ready,get fail")
            return {}
        return self.Client.Callapi('profile/get_profile',{'target_viewer_id':target_id})



