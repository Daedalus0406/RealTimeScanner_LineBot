import requests


def line_notify(message, counter):
    headers = {
            "Authorization": "Bearer " + "s2GQg4mQUleMowLu2FiNSyMM2NZiTCPUjZp2v64whqF",
            "Content-Type": "application/x-www-form-urlencoded"
        }

    counter = counter - 1
    params = {"message": message + "\n已過:" + str(counter) + "分鐘"}

    if message != " " and counter % 5 == 0:
        r = requests.post("https://notify-api.line.me/api/notify", headers=headers, params=params)
    else:
        r = None

    return r
