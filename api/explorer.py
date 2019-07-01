import datetime
import json
import config
import logging
from pymongo import MongoClient
import json
from bson import json_util
from bson.objectid import ObjectId
import traceback
from logging.handlers import TimedRotatingFileHandler
import types
from services import qmail
is_print_date = False
logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename='/tmp/log/hist.log',
                filemode='w')
logHandler = TimedRotatingFileHandler(filename = '/tmp/log/live_.log', when = 'D', interval = 1, encoding='utf-8')
logger = logging.getLogger('logger')
formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)


client = MongoClient(config.MONGODB_DB_URL)
db = client[config.MONGODB_DB_NAME]
logger.info(config.MONGODB_DB_URL)
logger.info(config.MONGODB_DB_NAME)
# qconn = q.q(host = config.Q_HOST, port = config.Q_PORT, user = config.Q_USER)
###################### Q functions ######################
import pandas as pd
from flatten_json import flatten
from services.celery import celery

import jsonify
# @cache.memoize(timeout= 3 )    
def Query(account,start, end, op_type_id, to_addr ):
    if start == 'null':
        return {'error_code':1, 'msg': 'start date can not be null'}
    if end == 'null':
        return {'error_code':2, 'msg': 'end date can not be null'}
    if op_type_id not in (0,1,2,4, 6,37):
        return {'error_code':3, 'msg': 'operation type not support'}
    logger.info('trying to query...')
    # task = Async_Query.apply_async(args = [account,start, end, op_type_id ])
    task = Async_Query.delay(account,start, end, op_type_id, to_addr)
    # task = test_async.apply_async()
    logger.info('task sent... with id '+ str(task.id))
    return {'task':task.id}


@celery.task(bind=True)
def test_async(self):
    logger.info('before sleep')
    time.sleep(5)
    logger.info('after sleep')
    return {}

@celery.task
def Async_Query(account,start, end, op_type_id ,to_addr):
    logger.info('cursor creating...')
    c = db.account_history.find({'bulk.account_history.account':account,'bulk.operation_type':op_type_id, 'bulk.block_data.block_time':{'$gte':start, '$lte':end} })
    res = []
    for j in c:
        d = {"op": j['op'], "block_num": j['bulk']["block_data"]["block_num"],
                      "timestamp": j['bulk']["block_data"]["block_time"]
                      }
        if op_type_id == 6:
            d['op'].pop('owner')
            d['op'].pop('active')
        tmp = flatten(d, '__')
        keys = list(tmp.keys())
        for k in keys:
            if 'extensions' in k or 'memo' in k:
                tmp.pop(k)
        res.append( tmp )
    c.close()
    logger.info('cursor finished!')
    if len(res) > 0:
        respd = pd.DataFrame(data = res, columns = res[0].keys())
    else:
        logger.info('no data found')
        respd = pd.DataFrame()
    filename = '_'.join([account,start,end,str(op_type_id)]) + '.csv'
    filepath = config.TODIR + '/'  + filename 
    respd.to_csv(filepath)
    qmail.mail(filepath, to_addr)
    logger.info('mail sent to '+ to_addr)
    return {'result':filename}

