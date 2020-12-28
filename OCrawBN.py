# !/usr/bin/python
# -*- coding: utf-8 -*-
import argparse
import datetime
import json
import sys
import time

import pymysql
import requests
import urllib3

# create temp_list storage data
temp_list = []


def ymd():
    time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    temp = time_str.split()
    return temp[0]


def out_header(path):
    string = '用户|订单|日期|时间戳|状态|col|金额'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(string + '\n')


def out(path, string):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(string + '\n')


def time_to_day(tsr):
    result = '%s' % (tsr.replace('-', ''))
    re = result.split()
    temp = re[0]
    return temp


def buyer(bsr):
    buyname = str(bsr).replace('|', '').strip()
    return buyname


def status(string, tuihuo):
    temp = str(string)

    if temp == 'portalsent':
        name = '待买家收货'
    elif temp == 'waitsellersend':
        name = '待发货'
    elif temp == 'cancel' and tuihuo is not None:
        name = tuihuo
    elif temp == 'cancel' and tuihuo is None:
        name = '已取消'
    elif temp == 'buyerreceived':
        name = '已完成'
    elif temp == 'sellersent':
        name = '待平台收货'
    elif temp == 'waitportalappraise':
        name = '待平台验货'
    elif temp == 'waitportalsend':
        name = '待平台发货'
    elif temp == 'waitack':
        name = '待买家付款'
    elif temp == 'waitpay':
        name = '待买家付款'
    else:
        name = temp

    return name


def o(c, st, et):
    # temp = []

    url_qj = '''
    https://api.ttjianbao.com/order/auth/sellerOrderList?pageNo=%s&isAssistant=1&pageSize=40&orderCode=&customerName=&minPrice=&maxPrice=&startTime=%s&endTime=%s&isLive=0&searchStatus=all&appVersion=3.2.1&imei=865166026560576&deviceVersion=5.1.1&deviceName=PCLM10&channel=yingyongbao&appId=android
    ''' % (c, st, et)

    urllib3.disable_warnings()

    header = {
        'user-agent': 'Mozilla/5.0 (Linux; U; Android 5.1.1; zh-cn; RMX1931 Build/LMY49I) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30',
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJwaG9uZSIsImp0aSI6IjQyODAxNTkiLCJwaG9uZSI6IjE3NjIzNDI2Njc4IiwiZXhwIjoxNjA5ODMyOTk4fQ.EDZKqweJKVoVOfVA5mUcdoy44Ll3Ov0amBZGzjRjbm4'

    }
    cookie = {'key': 'value'}

    r = requests.get(url_qj, headers=header, verify=False)

    con = r.json()
    t = json.dumps(con, ensure_ascii=False).encode(
        'gbk', 'ignore').decode('gbk')
    load = json.loads(t)
    result = load['data']
    # print (result)

    for i in result:
        d = dict(i)
        ts = '%s|%s|%s|%s|%s|%s|%s|%s|%s' % (
            buyer(d.get('buyerName')), d.get(
                'orderCode'), time_to_day(d.get('orderCreateTime')),
            d.get('orderCreateTime'),
            status(d.get('orderStatus'), d.get(
                'workorderDesc')), d.get('workorderDesc'),
            d.get('originOrderPrice'), d.get(
                'shippingCity'), d.get('shippingReceiverName')
        )

        out(pth, ts)
        temp_list.append(ts)
        print(ts)

    # d=dict(result[0])
    jug = len(result)
    print()
    print(jug)
    print()

    return jug


def runsql_ins(dlist):
    d = str(dlist).split('|')
    sql_insert = ''' insert into order_temp values("%s","%s","%s","%s",
    "%s","%s",%d,"%s","%s") 
    ;

    ''' % (d[0].strip(), d[1].strip(), d[2].strip(), d[3].strip(), d[4].strip(), d[5].strip(), float(d[6].strip()),
           d[7].strip(), d[8].strip())

    # print(sql_insert)
    conn = pymysql.connect(host='127.0.0.1', port=3306, user='root',
                           passwd='sakura928', db='world', charset='utf8')
    cursor = conn.cursor()
    cursor.execute(sql_insert)
    cursor.close()

    conn.commit()
    conn.close()


def runsql_cl():
    sql_clean = 'truncate table order_temp ;'

    # print(sql)
    conn = pymysql.connect(host='127.0.0.1', port=3306, user='root',
                           passwd='sakura928', db='world', charset='utf8')
    cursor = conn.cursor()
    cursor.execute(sql_clean)
    time.sleep(0.2)
    cursor.close()
    conn.close()


def runsql_count(std, etd):
    sql = ''' 
        SELECT d,'2_8' as tr,count(0) as sellnum,sum(amount) as sm FROM (select distinct * from world.order_temp) f
    where datetime>='%s 02:00:00' and datetime<'%s 08:00:00'
    and statu in ('待买家收货','待发货','已完成','待平台收货','待平台验货','待平台发货')
    group by d,tr
    union all
    SELECT d,'8_14' as tr,count(0) as sellnum,sum(amount) as sm FROM (select distinct * from world.order_temp) f
    where datetime>='%s 08:00:00' and datetime<'%s 14:00:00'
    and statu in ('待买家收货','待发货','已完成','待平台收货','待平台验货','待平台发货')
    group by d,tr
    union all
    SELECT d,'14_20' as tr,count(0) as sellnum,sum(amount) as sm FROM (select distinct * from world.order_temp) f
    where datetime>='%s 14:00:00' and datetime<'%s 20:00:00'
    and statu in ('待买家收货','待发货','已完成','待平台收货','待平台验货','待平台发货')
    group by d,tr
    union all
    SELECT d,'20_2 next day' as tr,count(0) as sellnum,sum(amount) as sm FROM (select distinct * from world.order_temp) f
    where datetime>='%s 20:00:00' and datetime<'%s 02:00:00'
    and statu in ('待买家收货','待发货','已完成','待平台收货','待平台验货','待平台发货')
    group by d,tr
    ;
        
    ''' % (std, std, std, std, std, std, std, etd)

    # print(sql)

    conn = pymysql.connect(host='127.0.0.1', port=3306, user='root',
                           passwd='sakura928', db='world', charset='utf8')

    cursor = conn.cursor()
    cursor.execute(sql)
    res = cursor.fetchall()
    # header = 'date timerange sellnum sm'
    print()

    for i in res:
        print('%s , %s , %d , %d' % (i[0], i[1], i[2], float(i[3])))

    cursor.close()
    conn.close()


def ifgone():
    if input('Go on ? ...... ') == 'c':
        print('Go to next ...')
        print()
    else:
        sys.exit(0)


def get_days(datalist):
    # timeday scoped
    tempday = []
    for i in datalist:
        d = str(i).split('|')[3].split()[0].strip()
        tempday.append(d)

    tds = list(set(tempday))
    scope = sorted(tds)

    # make adjust day range
    for i in range(1):
        st = datetime.datetime.strptime(scope[len(scope) - 1], '%Y-%m-%d')
        dt = (st + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        scope.append(dt)

    return scope


def make_days(begin, end):
    # timeday scoped
    tempday = []
    tempday.append(begin)
    tds = list(set(tempday))
    scope = sorted(tds)

    # make adjust day range
    for i in range(1, int(end)):
        st = datetime.datetime.strptime(begin, '%Y-%m-%d')
        dt = (st + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        scope.append(dt)

    return scope


# define parameter
parameter = argparse.ArgumentParser()
parameter.add_argument('-day', help="day time 20190609")
parameter.add_argument('-st', help="day time 20190609")
args = parameter.parse_args()
day_time = args.day

if day_time is None:
    print('argument -day: expected one argument ......')
    sys.exit()

date_notice = ymd()
pth = 'd:/out/bn/order%s.txt' % day_time
start = input("Date start like '%s':" % date_notice.strip())
# end = input("Date end like '%s':" % date_notice.strip())
end = input("How many days data needs extract ... enter a num: ")

print()
print('The out path: ' + pth)
print()

# appVersion=3.1.3&imei=865166023611018
c = 0
out_header(pth)

# if go here ,the data extract over !
spd = make_days(start.strip(), end.strip())

print(spd)

for i in spd:
    print(i)
    print()
    while True:
        v = o(c, i.strip(), i.strip())
        c += 1

        if v == 0:
            # counter set zero
            c = 0
            break

        time.sleep(5)

    time.sleep(11)

'''
while True:
    v = o(c, start.strip(), end.strip())
    c += 1

    if v == 0:
        break
    time.sleep(5)
    
'''

# list flush
new_temp_list = list(set(temp_list))
print(len(temp_list))
print(len(new_temp_list))

# choose path
ifgone()

# In normal temp_list can't be null
# clean temp table data
runsql_cl()

# insert temp table
for i in new_temp_list:
    runsql_ins(i)

# count results
sc = get_days(new_temp_list)
print(sc)
for i in range(len(sc) - 1):
    runsql_count(sc[i].strip(), sc[i + 1].strip())
