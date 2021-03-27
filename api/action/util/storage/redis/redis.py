# -*- coding: utf-8 -*-
import copy
import json
import json
import os
import asyncio
import time
import fcntl
import struct
import redis
import sys

class RedisClient():
    
    def __init__(self, username, password, db_index, timeout_time) -> None:
        # db_index for db selecting
        self._db_index    = db_index
        # every key-value will be expired after 30 sec, this value must larger than the IotReqeustServer Timeout Time
        self._expire_time = timeout_time
        # username and password for connecting to Redis
        self._username    = username
        self._password    = password
        self._grafana_qkey = "grafana_qkey"
        self._grafana_test_qkey = "grafana_test_qkey"
        self._log_path_prefix = '/tmp/';

    def lock_file(self, f):
        title = sys._getframe().f_code.co_name
        try:
            fcntl.lockf(f, fcntl.LOCK_EX)
        except (OSError, BlockingIOError) as error:
            print("["+title+"] fail to lock")
            return error

    def unlock_file(self, f):
        title = sys._getframe().f_code.co_name
        try:
            fcntl.lockf(f, fcntl.LOCK_UN)
        except (OSError, BlockingIOError) as error:
            print("["+title+"] fail to unlock")
            return error

    def writeFile(self, path, msg):
        #os.chmod(path, 511);
        title = sys._getframe().f_code.co_name
        with open(path, "a") as f:
            try:
                self.lock_file(f)
                f.write(msg)
            except Exception as error:
                print("["+title+"] fail to write file, error: %s" %(error))
                return False
            finally:
                #print("[writeFile] done")
                self.unlock_file(f)
        return True

    def _printLog(self, filepath, msg, mac, title=False):
        print(msg)
        path = filepath + mac
        new_msg = msg + "\n"
        self.writeFile(path, new_msg)
        return True

    def connect(self, host="127.0.0.1", port=6379):
        #
        # create redis pool (redis do not set any password now)
        #     decode_responses: let the value be str
        #     redis.Redis(): for connecting once
        #     redis.ConnectionPool(): create a long-standing connection
        #
        try:
            print("[Redis][connect] try to connect to Redis...")
            pool = redis.ConnectionPool(host=host, port=port, decode_responses=True, db=self._db_index)
            self._client = redis.Redis(connection_pool=pool)
            print("[Redis][connect] try to connect to Redis... done!")

            if not self._is_redis_available():
                print("[Redis][connect] can not ping Redis")
                return False
            return True
        except:
            return False

    def pushRequestIntoList(self, mac, params):
        try:
            if not self._is_redis_available():
                log_data = "[Redis][pushRequestIntoList] Redis is not available"
                self._printLog(str(self._log_path_prefix), log_data, mac, "pushRequestIntoList")
                return False

            print("[Redis][pushRequestIntoList] params: " + params)

            ts = int(time.time())
            log_data = "[Redis][pushRequestIntoList] push into RequestList"
            self._printLog(str(self._log_path_prefix), log_data, mac, "pushRequestIntoList")
            request_data_bundle_string = params

            # redis key - value will be: { control_uid_with_value : timestamp of request time }
            value = str(ts)
            success = self._set_key_value_with_check(request_data_bundle_string, value)
            print(success)

            if success == None:
                log_data = "[Redis][pushRequestIntoList]["+mac+"] fail to add key: " + str(request_data_bundle_string)
                self._printLog(str(self._log_path_prefix), log_data, mac, "pushRequestIntoList")
                return False

            log_data = "[Redis][pushRequestIntoList]["+mac+"] Done"
            self._printLog(str(self._log_path_prefix), log_data, mac, "pushRequestIntoList")
            return True

        except Exception as error:
            log_data = "[Redis][pushRequestIntoList] can not push into RequestList, error_log:%s" %(error)
            self._printLog(str(self._log_path_prefix), log_data, mac, "pushRequestIntoList")

    def getRequestCandidate(self):
        all_keys = self._find_all_key()
        if self._grafana_qkey in all_keys:
            all_keys.remove(self._grafana_qkey)
        candidate_arr = []
        for key in all_keys:
            candidate_arr.append(key)
            self._delete_value_by_key(key)

        return candidate_arr


    def pushUidIntoList(self, mac, params):
        # Construct control_uid
        #
        #   - control_uid of .ucl is composed by [gateway MAC];[sensor id];[sensor channel];[control_type];[previous_code];[expected_code];[request_id];[code_slot];[timestamp]
        # 
        #   - control_uid of .s is composed by   [gateway MAC];[sensor id];[sensor channel];[control_type];[origin_value];[expect_value];[timestamp]
        #                                         18CC23001EAF;    326    ;       0        ;       s      ;       0      ;       1      ; 1537408471
        #
        #     expected params for status change (doorlock open/close):
        #     {
        #      "control_type":   "s",
        #      "expect_value":   "1",
        #      "origin_value":   "0",
        #      "sensor_id":      "326",
        #      "sensor_channel": "0"
        #     }
        #
        #     expected params for usercode change:
        #     {
        #      "control_type":   "ucl",
        #      "expect_value":   "8523,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_",  (expected_code)
        #      "origin_value":   "_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_",     (previous_code)
        #      "sensor_id":      "317",
        #      "sensor_channel": "0",
        #      "request_id":     "bb8deb",
        #      "code_slot":      "0"
        #     }

        if not self._is_redis_available():
            print("[Redis][pushUidIntoList] Redis is not available")
            return False

        ts = int(time.time())

        try:
            control_type = params['control_type']
            print("[Redis][pushUidIntoList]["+mac+"]["+str(ts)+"] control_type: "+control_type)

            print(params)
            if control_type == "s":
                expect_value   = params['expect_value']
                origin_value   = params['origin_value']
                sensor_id      = params['sensor_id']
                sensor_channel = params['sensor_channel']
                control_uid_with_value = mac + ";" + str(sensor_id) + ";" + str(sensor_channel) + ";" + control_type + ";" + origin_value + ";" + expect_value + ";" + str(ts)
            elif control_type == "ucl":
                # ex: {
                # "sensor_id": "345", 
                # "sensor_channel": "0", 
                # "expect_value": "2073,1233,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_", 
                # "request_id": "318e71", 
                # "control_type": "ucl", 
                # "origin_value": "2073,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_", 
                # "code_slot": "1"
                # }
                expect_value   = params['expect_value']
                origin_value   = params['origin_value']
                sensor_id      = params['sensor_id']
                sensor_channel = params['sensor_channel']
                request_id     = params['request_id']
                code_slot      = params['code_slot']
                control_uid_with_value = mac + ";" + str(sensor_id) + ";" + str(sensor_channel) + ";" + control_type + ";" + origin_value + ";" + expect_value + ";" + request_id + ";" + str(code_slot) + ";" + str(ts)
                print("[Redis][pushUidIntoList]["+mac+"]["+str(ts)+"] control_uid_with_value: " + control_uid_with_value)
        except:
            print("[Redis][pushUidIntoList]["+mac+"]["+str(ts)+"] fail to push control id into timeout list")
            return False
        print("[Redis][pushUidIntoList]["+mac+"] try to push data into Timeout list")

        # redis key - value will be: { control_uid_with_value : timestamp of request time }
        value = str(ts)
        success = self._set_key_value_with_check(control_uid_with_value, value)
        print(success)

        if success == None:
            print("[Redis][pushUidIntoList]["+mac+"] fail to add key: " + str(control_uid_with_value))
            return False

        print("[Redis][pushUidIntoList]["+mac+"] Done")
        return True

    def removeUidFromList(self, mac, params):
        if not self._is_redis_available():
            print("[Redis][removeUidFromList] Redis is not available")
            return False
        ts = int(time.time())
        try:
            control_type   = params['control_type']
            sensor_id      = params['sensor_id']
            sensor_channel = params['sensor_channel']
            control_id = mac + ";" + sensor_id + ";" + sensor_channel + ";" + control_type

        except:
            print("[Redis][removeUidFromList]["+mac+"]["+str(ts)+"] fail to remove control id from timeout list")
            return False

        find_keys = self._find_key_by_fossy(control_id + "*")
        print("[Redis][removeUidFromList]["+mac+"]["+str(ts)+"] find_keys:")
        print(find_keys)
        try:
            if len(find_keys) == 1:
                if self._check_key_exist(find_keys[0]):
                    self._delete_value_by_key(find_keys[0])
                    print("[Redis][removeUidFromList]["+mac+"]["+str(ts)+"] Done")
                else:
                    print("[Redis][removeUidFromList]["+mac+"]["+str(ts)+"] Do not need to remove the control_id")

            elif len(find_keys) > 1:
                print("[Redis][removeUidFromList]["+mac+"]["+str(ts)+"] Error! there are 2 control_id in the DB, remove all")
                for key in find_keys:
                    if self._check_key_exist(key):
                        self._delete_value_by_key(key)
            else:
                # do not need to remove control_id in the DB
                print("[Redis][removeUidFromList]["+mac+"]["+str(ts)+"] do not need to remove control_id in the DB")
                return True
        except:
            print("[Redis][removeUidFromList]["+mac+"]["+str(ts)+"] Error! can not remove key")
            return False

        return True

    def checkValidUidInList(self, mac, params):
        #
        # check if the uid exist in DB
        # if the uid exist in DB, return False (invalid)
        # if not, return True (valid)
        #
        if not self._is_redis_available():
            print("[Redis][checkValidUidInList] Redis is not available")
            return False

        ts = int(time.time())

        try:
            control_type   = params['control_type']
            sensor_id      = params['sensor_id']
            sensor_channel = params['sensor_channel']
            control_id = mac + ";" + sensor_id + ";" + sensor_channel + ";" + control_type 

        except Exception as error:
            print("[Redis][checkValidUidInList]["+mac+"]["+str(ts)+"] fail to parse data, err_msg:" + str(error))
            return False

        find_keys = self._find_key_by_fossy(control_id)
        print("[Redis][checkValidUidInList]["+mac+"]["+str(ts)+"] find_keys:")
        print(find_keys)

        if len(find_keys) > 0:
            return False

        print("[Redis][checkValidUidInList]["+mac+"]["+str(ts)+"] Done")
        return True

    def checkMatureTime(self, timeout_time):
        if not self._is_redis_available():
            print("[Redis][checkMatureTime] Redis is not available")
            return False

        ts = int(time.time())
        hit_timeout_arr = []
        hatching_arr = []

        all_keys = self._find_all_key()
        if self._grafana_qkey in all_keys:
            all_keys.remove(self._grafana_qkey)
        #print("[Redis][checkMatureTime] all_keys:")
        #print(all_keys)

        for key in all_keys:
            timestamp_value = self._get_value_by_key(key)
            if len(timestamp_value) > 0:
                timestamp_value_int = int(timestamp_value)
                if (ts - timestamp_value_int) >= timeout_time:
                    hit_timeout_arr.append(key)
                    self._delete_value_by_key(key)

        #print("[Redis][checkMatureTime] timeout keys:")
        #print(hit_timeout_arr)
        return hit_timeout_arr;

    def updateVersionNum(self, key, ver_num):
        # check if the key exist in the DB.
        #   1. if the key do not exist, set the value (version_number)
        #   2. if the key exist in the DB, 
        #      get the value (version_number) of the key 
        #      and compare the value (version_number) with the new version_number
        try:
            if not self._check_key_exist(key):
                self._set_key_value_without_expire(key, ver_num)
                return True
            else:
                value = self._get_value_by_key(key)
                old_ver_num = int(value)
                new_ver_num = int(ver_num)
                if new_ver_num > old_ver_num:
                    print("[Redis][updateVersionNum] new_ver_num: " + ver_num + " > old_ver_num: " + value + ", update VersionNum!")
                    self._set_key_value_without_expire(key, ver_num)
                    return True
                else:
                    print("[Redis][updateVersionNum] new_ver_num: " + ver_num + " < old_ver_num: " + value + ", do no need to update VersionNum!")
                    return False
        except:
            print("[Redis][updateVersionNum] can not deal with VersionNum")
            return False

    def forceUpdateVersionNum(self, key, ver_num):
        try:
            if not self._check_key_exist(key):
                print("[Redis][forceUpdateVersionNum] new_ver_num: " + ver_num + ", force update VersionNum!")
                self._set_key_value_without_expire(key, ver_num)
                return True
            else:
                value = self._get_value_by_key(key)
                old_ver_num = int(value)
                new_ver_num = int(ver_num)
                print("[Redis][forceUpdateVersionNum] new_ver_num: " + ver_num + ", old_ver_num: " + value + ", force update VersionNum!")
                self._set_key_value_without_expire(key, ver_num)
                return True

        except:
            print("[Redis][forceUpdateVersionNum] can not deal with VersionNum")
            return False

    def fulshDb(self):
        return self._flush_all_data_in_slected_db()

    def checkDbAvailable(self):
        return self._is_redis_available()

    def putIntoGrafanaQueue(self, log_data, mac, title):
        item = "{};{};{}".format(log_data, mac, title)
        put_status = True
        try:
            self._put_item_into_queue_tail(item, self._grafana_qkey)
        except:
            print("[Redis][putIntoGrafanaQueue] fails")
            put_status = False
        return put_status

    def isGrafanaQueueEmpty(self):
        return self._get_queue_len(self._grafana_qkey) == 0

    def getGrafanaQueue(self):
        item = self._get_item_from_queue_head(self._grafana_qkey)
        try:
            log_data, mac, title = item.split(";")
        except:
            token = item.split(";")
            if len(token) > 3:
                log_data = token[0]
                mac = token[1]
                title = token[2]
            else:
                log_data = token[0] if len(token) > 0 else ""
                mac = token[1] if len(token) > 1 else ""
                title = token[2] if len(token) > 2 else ""
        return log_data, mac, title

    # ======= Redis Utilities =======

    def _get_redis_info(self, topic):
        return True

    def _set_key_value_without_expire(self, key, value):
        return self._client.set(key, value)

    def _set_key_value(self, key, value):
        return self._client.set(key, value, ex=self._expire_time)

    def _set_key_value_with_check(self, key, value):
        # if the key exist, retrun None, if not, return True
        print("[Redis][_set_key_value_with_check] set:{ " + key + ", " + value + " }")
        return self._client.set(key, value, ex=self._expire_time, nx=True)

    def _get_value_by_key(self, key):
        return self._client.get(key)

    def _check_key_exist(self, key):
        return self._client.exists(key)

    def _delete_value_by_key(self, key):
        return self._client.delete(key)

    def _find_key_by_fossy(self, key):
        # usage:
        #   KEYS *       : match all keys with the pattern key*
        #   KEYS h?llo   : match hello, hallo and hxllo etc
        #   KEYS hllo    : match hllo and heeeeello etc
        #   KEYS h[ae]llo: match hello and hallo, but do not match hillo
        return self._client.keys(key)

    def _find_all_key(self):
        return self._client.keys()

    def _set_expire(self, key, time):
        return self._client.expire(key, time=time)

    def _key_rename(self, old_key_name, new_key_name):
        return self._client.rename(old_key_name, new_key_name)

    def _check_type(self, key):
        return self._client.type(key)

    def _flush_all_data_in_slected_db(self):
        # flush only slected db in Redis
        self._client.flushdb()

    def _flush_all_data_in_all_db(self):
        # Warning! flush all dbs in Redis
        self._client.flushall()

    # assuming rs is your redis connection
    def _is_redis_available(self):
        # ... get redis connection here, or pass it in. up to you.
        try:
            ping_status = self._client.ping()  # getting None returns None or throws an exception
            if ping_status != True:
                return False
        #except (redis.exceptions.ConnectionError,
        #        redis.exceptions.BusyLoadingError):
        except Exception as error:
            mac = "error"
            log_data = "[_is_redis_available][exception] %s\n" %(str(error))
            self._printLog(str(self._log_path_prefix), log_data, mac, "_is_redis_available")
            return False
        return True

    def lock_file(self, f):
        return True

    def unlock_file(self, f):
        return True

    def close(self):
        return True

    def _put_item_into_queue_tail(self, item, qkey):
        self._client.rpush(qkey, item)

    def _get_queue_len(self, qkey):
        return self._client.llen(qkey)

    def _get_item_from_queue_head(self, qkey):
        return self._client.lpop(qkey)

    def test_redis_memory(self, log_data, mac, title):
        if not self._is_redis_available():
            log = "===== [Redis][test_redis_memory] Redis is not available ====="
            print(log)
            self._printLog(str(self._log_path_prefix), log, mac, "test_redis_memory")
            return False

        item = "{};{};{}".format(log_data, mac, title)
        put_status = True
        try:
            self._put_item_into_queue_tail(item, self._grafana_test_qkey)
        except:
            print("[Redis][test_redis_memory] fails")
            put_status = False
        return put_status