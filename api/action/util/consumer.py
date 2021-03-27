from threading import Thread
import threading
import sys
import os
from confluent_kafka import Consumer, KafkaException, KafkaError, Producer, TopicPartition
# chdir to script dir
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
__DIR__ = dname
os.chdir(dname)
import subprocess
import json
import signal
import tempfile
import datetime

# prepare log folder
_ERROR_LOG_FILE = 'DEBUG.log';
_LOG_FOLDER = '/tmp/Consumer/';
_UPLOAD_DATA_PATH = '/tmp/Consumer/upload_data/'
_LOG_PATH_PREFIX = _LOG_FOLDER
if not os.path.exists(_LOG_FOLDER):
    try:
        os.makedirs(_LOG_FOLDER)
    except FileExistsError:
        # directory already exists
        pass

if os.access(_LOG_FOLDER, os.W_OK) == False:
    os.chmod(_LOG_FOLDER, 511)

if not os.path.exists(_UPLOAD_DATA_PATH):
    try:
        os.makedirs(_UPLOAD_DATA_PATH)
    except FileExistsError:
        pass

if os.access(_UPLOAD_DATA_PATH, os.W_OK) == False:
    os.chmod(_UPLOAD_DATA_PATH, 511)

# logging
import logging
from logging.handlers import RotatingFileHandler
my_handler = RotatingFileHandler('/tmp/Consumer/consumer.log', mode='a', maxBytes=100*1024*1024, backupCount=2, encoding=None, delay=0)
logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] %(message)s', handlers=[my_handler])

# leak protection
import mem
consume_count = 0
detect_count = 50000
mem_threshold = 300.0*1024.0*1024.0

from typing import cast
from urllib.parse import urlparse, parse_qs
from requests.adapters import HTTPAdapter
from threading import Timer
from threading import Lock
import requests
import copy
import time
import gc
import random
import fcntl
import atexit
import urllib
import asyncio
import time
import csv
import codecs
# -*- coding: utf-8 -*-

_SHOULD_SEND_LOG_SERVER = True

# ========== Test Internet ===========
def checkInternet():
    global _SHOULD_SEND_LOG_SERVER
    url = 'http://www.google.com/'
    title = sys._getframe().f_code.co_name
    timeout = 10
    try:
        _ = requests.get(url, timeout=timeout)
        _SHOULD_SEND_LOG_SERVER = True
        print("[{}] Successfully access Internet, need to send log to log server".format(title))
        return True
    except requests.ConnectionError:
        print("[{}] Can not access Internet, do not need to send log to log server".format(title))
        _SHOULD_SEND_LOG_SERVER = False
        return False


# ============= KAFKA URL =============
#
# check the environment is sandbox or live
#
def appendDefaultIP():
    title = sys._getframe().f_code.co_name
    if os.path.isdir("/temp/api/action/"):
        print("[%s] The environment is docker" % title)

        # push content into /etc/hosts
        # #kafka
        # 127.0.0.1 kafka_1
        # 127.0.0.1 kafka_2
        # 127.0.0.1 kafka_3
        # 127.0.0.1 Redis
        # 127.0.0.1 localhost

        fname = "/etc/hosts"
        new_file_content = ""
        tag_exist = False
        with open(fname) as f:
            content = f.readlines()
        for index in range(len(content)):
            if content[index].find("kafka_1") == -1 and content[index].find("kafka_2")   == -1 and \
               content[index].find("kafka_3") == -1 and content[index].find("kafka")     == -1 and \
               content[index].find("Redis")   == -1 and content[index].find("localhost") == -1:
                new_file_content += content[index]

        # assign new kafka url into the etc hosts
        addition_kafka_url = "#kafka\n127.0.0.1 kafka_1\n127.0.0.1 kafka_2\n127.0.0.1 kafka_3\n127.0.0.1 Redis\n127.0.0.1 localhost"
        new_file_content += addition_kafka_url
        with open(fname, "w") as f:
            try:
                if len(new_file_content) > 0:
                    f.write(new_file_content)
                    print("[%s] Successfully modify etc/hosts" % title)
            except:
                print("[%s] Can not modify etc/hosts" % title)

    else:
        print("[%s] The environment is live" % title)

_exit_flag = False
_is_test = False

# ============= UTILITY =============

@atexit.register # exitHook
def Exit():
    global _exit_flag
    _exit_flag = True
    send_log_server = False
    title = sys._getframe().f_code.co_name
    log_data = "[{}] Close Consume Worker!".format()
    lot_id = "system"
    printLog(str(_LOG_PATH_PREFIX), log_data, lot_id, send_log_server, title)

def postToLogServer(log_msg, title):
    return True

def parseUrl(url):
    output = urlparse(url)
    return output

def lock_file(f):
    title = sys._getframe().f_code.co_name
    try:
        fcntl.lockf(f, fcntl.LOCK_EX)
    except (OSError, BlockingIOError) as error:
        print("["+title+"] fail to lock")
        return error

def unlock_file(f):
    title = sys._getframe().f_code.co_name
    try:
        fcntl.lockf(f, fcntl.LOCK_UN)
    except (OSError, BlockingIOError) as error:
        print("["+title+"] fail to unlock")
        return error

def writeFile(path, msg):
    #os.chmod(path, 511);
    title = sys._getframe().f_code.co_name
    with open(path, "a") as f:
        try:
            lock_file(f)
            f.write(msg)
        except:
            print("["+title+"] fail to write file")
            return False
        finally:
            #print("[writeFile] done")
            unlock_file(f)
    return True

def printLog(filepath, msg, t_id, log_server=False, title=False):
    print(msg)
    path = filepath + t_id
    new_msg = msg + "\n"
    writeFile(path, new_msg)
    if log_server:
        if not postToLogServer(msg, title):
            return False
    return True

def _exit():
    try:
        Exit()
        sys.exit(0)
    except SystemExit:
        print('SystemExit')
        os._exit(0)

_WORKER_NUMBER = -1
try:

    argv_list = sys.argv
    if len(argv_list) < 2:
        print("[ERROR] argv < 2")
        print("========================================================================")
        print("[INFO] Usage: sudo python3 consumer.py $worker_number")
        print("========================================================================")

    if len(argv_list) > 1:
        worker_num = sys.argv[1]
        print("[INFO] Worker number: " + worker_num)
    else:
        worker_num = "1"
        print("[INFO] use default worker number: " + str(worker_num))

    _WORKER_NUMBER = worker_num

    if worker_num.isdigit() == False and _is_test == False:
        _exit()

    if worker_num == "1":
        db_index = [0]
    elif worker_num == "2":
        db_index = [0]
    else:
        print("[INFO] Worker number error! Worker number shoud be 1~5")
        _exit()
    print("[INFO] db_index: " + json.dumps(db_index))

except Exception as error:
    print("[ERROR] can not get argv, error: " + str(error))
    try:
        Exit()
        sys.exit(0)
    except SystemExit:
        print('SystemExit')
        os._exit(0)

_initial_timestamp = datetime.datetime.now()


# ==================== Others ====================
requests.adapters.DEFAULT_RETRIES = 5

def memory_leak_check():
    global consume_count
    global detect_count
    global mem_threshold
    consume_count = consume_count + 1
    if consume_count < detect_count:
        return
    consume_count = 0
    current_memroy_usage = mem.memory()
    if current_memroy_usage > mem_threshold:
        # memory usage too high, kill self
        sys.exit()
        os.kill(os.getpid(), signal.SIGKILL)


# ------------------------------ Initialize -----------------------------
checkInternet()
appendDefaultIP()
# -----------------------------------------------------------------------

def ConsumeTopic(topic, callback):
    global _WORKER_NUMBER
    c = Consumer({'bootstrap.servers': 'kafka_1,kafka_2,kafka_3', 'group.id': 'default', 'session.timeout.ms': 6000, 'default.topic.config': {'auto.offset.reset': 'latest'}})
    # Subscribe to topic
    # _WORKER_NUMBER will be 1 / 2
    # partition id will be 0 / 1
    #c.assign([TopicPartition(topic, int(_WORKER_NUMBER)-1)]) #fixed partition id
    c.subscribe([topic]) # random partition id
    print("=== ConsumeTopic launch ===")

    try:
        while True:
            msg = c.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                # Error or event
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition event
                    sys.stderr.write('%% %s [%d] reached end at offset %d, error msg:%s\n' % (msg.topic(), msg.partition(), msg.offset(), msg.error()))
                elif msg.error():
                    # Error
                    raise KafkaException(msg.error())
            else:
                # Proper message
                print(msg);
                sys.stderr.write('%% %s [%d] at offset %d with key %s:\n' % (msg.topic(), msg.partition(), msg.offset(), str(msg.key())))
                callback(msg.partition(), msg.key(), msg.value())
                memory_leak_check()
    except Exception as e:
        sys.stderr.write('exception: %s\n' % str(e))
        pass

    print("Close down consumer to commit final offsets.")
    # Close down consumer to commit final offsets.
    c.close()

# ------------------------------- Tools -------------------------------
def _sessionPost(url, data, timeout):
    title = sys._getframe().f_code.co_name
    sess = requests.session()
    sess.keep_alive = False
    response = sess.post(url, data=data, timeout=timeout)
    return response

def doTest(partition, key, value):
    send_log_server = _SHOULD_SEND_LOG_SERVER
    title = sys._getframe().f_code.co_name
    lot_id = "error"
    gpu_id = str(partition)
    
    now_timestamp = datetime.datetime.now()
    print("["+title+"][" + str(now_timestamp) + "] partition:" + str(partition))
    print("["+title+"] value:")
    print(value)

    # ----------- pasrse data ------------
    try:
        body = json.loads(value)
        lot_id = body['id']
        log_data = "["+title+"]["+lot_id+"]["+str(now_timestamp)+"] id:" + str(lot_id)
        printLog(str(_LOG_PATH_PREFIX), log_data, lot_id, send_log_server, title)
    except Exception as error:
        log_data = "["+title+"][" + str(now_timestamp) + "] can not parse id"
        printLog(str(_LOG_PATH_PREFIX), log_data, lot_id, send_log_server, title)
        return

# -------------- utility --------------

def taskPiper(partition, key, value):
    send_log_server = _SHOULD_SEND_LOG_SERVER
    title = sys._getframe().f_code.co_name
    now_time = datetime.datetime.now()
    value = value.decode("utf-8")
    key = key.decode("utf-8")
    print("["+title+"][" + str(now_time) + "] partition:" + str(partition) + ", key:" + str(key))

    # ----------- pasrse data ------------
    # HTTP POST
    try:
        if key == "posttest":
            doTest(partition, key, value)
        else:
            print("the key is out of range")
        return
    except Exception as e:
        print(str(e))
        log_data = "["+title+"] Error!"
        lot_id = "error"
        printLog(str(_LOG_PATH_PREFIX), log_data, lot_id, send_log_server, title)
        return

def Start():
    # Consumer
    global _is_test
    send_log_server = _SHOULD_SEND_LOG_SERVER
    title = sys._getframe().f_code.co_name
    lot_id = "system"
    if _is_test == False:
        log_data = "["+title+"] Consumer Start!"
        printLog(str(_LOG_PATH_PREFIX), log_data, lot_id, send_log_server, title)
        _consumer = Thread(target=ConsumeTopic, args=('TEST_REQUEST', taskPiper))
        _consumer.start()

    if _is_test == False:
        _consumer.join()

if __name__ == "__main__":
    try:
        Start()
    except KeyboardInterrupt:
        print('KeyboardInterrupt')
        try:
            Exit()
            sys.exit(0)
        except SystemExit:
            print('SystemExit')
            os._exit(0)
