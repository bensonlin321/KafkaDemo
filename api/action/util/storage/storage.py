# -*- coding: utf-8 -*-
import json
import os
import asyncio
import time
import fcntl
import struct
from gateway.redis.redis import RedisClient

class Storage():
    def __init__(self, storage_type, DB_path=False, log_dir=False, username=False, password=False, db_index=False, timeout_time=False):
        if storage_type == "redis":
            self.storage_client = RedisClient(username, password, db_index, timeout_time)
        else:
            print("some other storages")

    def connect(self, host, port):
        return self.storage_client.connect(host, port)

    def lock_file(self, f):
        return self.storage_client.lock_file(f)

    def unlock_file(self, f):
        return self.storage_client.unlock_file(f)

    def fulshDb(self):
        return self.storage_client.fulshDb()

    def checkDbAvailable(self):
        return self.storage_client.checkDbAvailable()

    def updateVersionNum(self, key, ver_num):
        return self.storage_client.updateVersionNum(key, ver_num)

    def forceUpdateVersionNum(self, key, ver_num):
        return self.storage_client.forceUpdateVersionNum(key, ver_num)

    def pushUidIntoList(self, mac, params):
        return self.storage_client.pushUidIntoList(mac, params)

    def getRequestCandidate(self):
        return self.storage_client.getRequestCandidate()

    def pushRequestIntoList(self, mac, params):
        return self.storage_client.pushRequestIntoList(mac, params)

    def removeUidFromList(self, mac, params):
        return self.storage_client.removeUidFromList(mac, params)

    def checkValidUidInList(self, mac, params):
        #
        # check if the uid exist in Timeout list
        # if the uid exist in DB, return False (invalid)
        # if not, return True (valid)
        #
        return self.storage_client.checkValidUidInList(mac, params)

    def checkMatureTime(self, timeout_time):
        return self.storage_client.checkMatureTime(timeout_time)

    def putIntoGrafanaQueue(self, log_data, mac, title):
        return self.storage_client.putIntoGrafanaQueue(log_data, mac, title)

    def isGrafanaQueueEmpty(self):
        return self.storage_client.isGrafanaQueueEmpty()

    def getGrafanaQueue(self):
        return self.storage_client.getGrafanaQueue()

    def test_redis_memory(self, log_data, mac, title):
        return self.storage_client.test_redis_memory(log_data, mac, title)
