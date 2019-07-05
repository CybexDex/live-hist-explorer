import datetime
from services.bitshares_websocket_client import BitsharesWebsocketClient, client as bitshares_ws_client_factory
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
from services.cache import cache



is_print_date = False
logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename='/tmp/log/live_.log',
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

assetMap = {}
accountMap = {}
logger.info('global:'+ str(id(assetMap)))
def _get_account(account_id):
    bitshares_ws_client = bitshares_ws_client_factory.get_instance()
    res = bitshares_ws_client.request('database', 'get_accounts', [[account_id]])
    bitshares_ws_client.close()
    return res[0]


def _is_object(string):
    return len(string.split(".")) == 3

def _get_asset(asset_id):
    asset = None
    bitshares_ws_client = bitshares_ws_client_factory.get_instance()
    asset = bitshares_ws_client.request('database', 'get_assets', [[asset_id], 0])[0]
    # dynamic_asset_data = bitshares_ws_client.get_object(asset["dynamic_asset_data_id"])
    # asset["current_supply"] = dynamic_asset_data["current_supply"]
    # asset["confidential_supply"] = dynamic_asset_data["confidential_supply"]
    # asset["accumulated_fees"] = dynamic_asset_data["accumulated_fees"]
    # asset["fee_pool"] = dynamic_asset_data["fee_pool"]

    # issuer = bitshares_ws_client.get_object(asset["issuer"])
    # asset["issuer_name"] = issuer["name"]
    bitshares_ws_client.close()

    return asset


@cache.memoize(timeout= 600 )    
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
def get_result(task_id):
    result = celery.AsyncResult(task_id)
    return result.result

@celery.task(bind=True)
def test_async(self):
    logger.info('before sleep')
    time.sleep(5)
    logger.info('after sleep')
    return {}

LIMIT = 100000
testMap = {'1':5}
def fulfillAccountMap(k):
    if k in accountMap:
        return accountMap[k]
    else:
        logger.info(k)
        t = _get_account(k)
        accountMap[k] = t['name']
        return accountMap[k]


def fulfillAssetMap(k):
    logger.info('fulfillAssetMap:'+ str(id(assetMap)))
    if k in assetMap:
        return assetMap[k]
    else:
        logger.info(k)
        t = _get_asset(k)
        assetMap[k] = (t['symbol'],t['precision'])
        logger.info(json.dumps(assetMap))
        return assetMap[k]

@celery.task
def Async_Query(account,start, end, op_type_id ,to_addr):
    logger.info('cursor creating...')
    logger.info('Async_Query:'+ str(id(assetMap)))
    c = db.account_history.find({'bulk.account_history.account':account,'bulk.operation_type':op_type_id, 'bulk.block_data.block_time':{'$gte':start, '$lte':end} })
    res = []
    page = 0
    files = []
    filename_base = '_'.join([account,start,end,str(op_type_id)])

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
                continue
            if k[-8:] == 'asset_id':
                kroot = k[:-8]
                kamount = kroot + 'amount'
                kasset_name = kroot + 'asset_name'
                fulfillAssetMap(tmp[k])
                tmp[kasset_name] = assetMap[tmp[k]][0]
                if kamount in keys:
                    tmp[kamount] = float(tmp[kamount]) / (10 ** assetMap[tmp[k]][1])
            if k[-10:] == 'account_id':
                kroot = k[:-10]
                kaccount_name = kroot + 'account_name'
                tmp[kaccount_name] = fulfillAccountMap(tmp[k])
            if op_type_id == 1 and k[-6:] == 'seller':
                kroot = k[:-6]
                kaccount_name = kroot + 'seller_name'
                tmp[kaccount_name] = fulfillAccountMap(tmp[k])
            if op_type_id == 0 and k[-4:] == 'from':
                kroot = k[:-4]
                kaccount_name = kroot + 'from_account_name'
                tmp[kaccount_name] = fulfillAccountMap(tmp[k])
            if op_type_id == 0 and k[-2:] == 'to':
                kroot = k[:-2]
                kaccount_name = kroot + 'to_account_name'
                tmp[kaccount_name] = fulfillAccountMap(tmp[k])
            if k[-7:] == 'account':
                kroot = k[:-7]
                kaccount_name = kroot + 'account_name'
                tmp[kaccount_name] = fulfillAccountMap(tmp[k])
        res.append( tmp )
        if len(res) >= LIMIT:
            respd = pd.DataFrame(data = res, columns = res[0].keys())
            filename = filename_base + '_page' + str(page) + '.csv'
            filepath = config.TODIR + '/'  + filename 
            respd.to_csv(filepath)
            files.append(filepath)
            page += 1
            res = []
        else:
            continue
    c.close()
    if len(res) > 0:
        respd = pd.DataFrame(data = res, columns = res[0].keys())
    else:
        respd = pd.DataFrame()
        logger.info('no data found, no email sent!')
    filename = filename_base + '_page' + str(page) + '.csv'
    filepath = config.TODIR + '/'  + filename 
    respd.to_csv(filepath)
    files.append(filepath)
    logger.info('cursor finished!')
    qmail.mail(files, to_addr)
    logger.info('mail sent to '+ to_addr)
    return {'result': filename_base + '*.csv','status': 'Task completed!'}



