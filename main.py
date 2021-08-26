"""
NOTE:
    測試修改變量
    75:end_time / 80:start_time / 129:time.sleep(X)
"""

import time
import requests
import pandas as pd
import numpy as np
import datetime
import Status_Analyzer as sa
import line_notify as ln


def datetime_timestamp(dt):
    time.strptime(dt, '%Y-%m-%d %H:%M:00')
    s = time.mktime(time.strptime(dt, '%Y-%m-%d %H:%M:00'))
    return int(s)


# Grafana資料擷取
user = 'tuser'
password = 'tuser'

ip = 'http://203.75.178.67:8080/api/datasources/proxy/1/'
# ip = 'http://10.105.1.124:8080/api/datasources/proxy/1/'
name = 'iotdbfa'
measure = 'tank'
ad = ['vpi3860', 'vpi3600', 'vpi2400']



def crawler(dbip, dbname, measurement, address, timestamp1, timestamp2):
    url = f"{dbip}query?db={dbname}&q=SELECT * FROM \"{measurement}\" WHERE \"device\"= \'{address}\' " \
          f"and time >= {timestamp1} and time <= {timestamp2}"

    return url





def report_df(js_list):
    col = js_list["results"][0]["series"][0]["columns"]
    df = pd.DataFrame(js_list["results"][0]["series"][0]["values"], columns=col)

    columns_drop = ['DI', 'DO', 'data17', 'data18', 'data19', 'data2', 'data20', 'data21', 'data22', 'device',
                    'device_1',
                    'ice_twmp', 'liquid', 'resin_pressure', 'resin_temp', 'resin_vacuum', 'ch1', 'ch2', 'ch3', 'ch4',
                    'ch5',
                    'ch6']
    df = df.drop(columns_drop, axis=1)
    # 整理時間欄位
    df['time'] = df['time'].str.replace('T', ' ').str.replace('Z', '')
    df['time'] = pd.to_datetime(df['time'], format="%Y-%m-%d %H:%M")
    df['time'] = (df['time'] + datetime.timedelta(hours=8))
    # 設置真空壓力狀態值
    vac_bins = [0, 3, 680, 900]
    vac_labels = [0, 1, 2]
    # vac_labels = ['low','P','high']
    df['vac_status'] = pd.cut(x=df.infusion_vacuum, bins=vac_bins, labels=vac_labels)

    pre_bins = [-np.inf, 0.003, 0.08, 6, np.inf]
    pre_labels = [0, 1, 2, 3]
    # pre_labels = ['buttom','dropping','rsing_start','drop_start']
    df['pre_status'] = pd.cut(x=df.infusion_pressure, bins=pre_bins, labels=pre_labels)
    # df.set_index("time", inplace=True)
    # df.to_csv("test_" + vpi_ad + ".csv")
    return df


flag_list = [0, 0, 0]
time_list = [2, 2, 2]
end_time = "2021-05-19 08:45:00"
# end_time = end_time = (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:00")
time_out = 1
while(True):


    start_time = (datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:00') + datetime.timedelta(hours=0, minutes=-4)).strftime("%Y-%m-%d %H:%M:00")
    # print(end_time)

    # 起始時間轉換
    start_stamp = datetime_timestamp(start_time)
    end_stamp = datetime_timestamp(end_time)
    start = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:00')

    # 照分鐘切割DF子集
    mins = [''] * 4
    for q in range(len(mins)):
        mins[q] = (start + datetime.timedelta(minutes=q)).strftime("%H:%M:%S")

    time1 = str(start_stamp) + 's'
    time2 = str(end_stamp) + 's'

    # DB連線
    url_3800 = crawler(ip, name, measure, ad[0], time1, time2)
    # url_3600 = crawler(ip, name, measure, ad[1], time1, time2)
    # url_2400 = crawler(ip, name, measure, ad[2], time1, time2)

    r_3800 = requests.get(url=url_3800, params='iotdbfa', auth=(user, password))
    # r_3600 = requests.get(url=url_3600, params='iotdbfa', auth=(user, password))
    # r_2400 = requests.get(url=url_2400, params='iotdbfa', auth=(user, password))


    # 確認連線
    if r_3800.status_code == 200:
        print('VPI3800連線成功', end_time)
        print("=" * 20)

    js = [r_3800.json(), 0, 0]

    if js[0] != {"results": [{"statement_id": 0}]}:
        print("vpi3800狀態:")
        report_38 = report_df(js[0])
        flag_list[0], time_list[0] = sa.status_analyzer(report_38, flag_list[0], time_list[0], ad[0])
        print("=" * 20)
        time_out = 1

    else:
        print("vpi3800無資料")
        print("=" * 20)
        ln.line_notify("vpi3800無資料", time_out)
        time_out = time_out + 1

    end_time = (datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:00') + datetime.timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:00")

    time.sleep(1)  # default:60 test:1
