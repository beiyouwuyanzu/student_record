from config import students
from redis_tool import r
from datetime import date
import datetime

def keep_day(l):
    d = 0
    for x in l[1: ]:
        if x != "已打卡":
            return d
        else:
            d += 1
    return d

def get_rank_data():
    mp = {}
    days = []

    today = date.today()
    for i in range(0, -14, -1):
        days.append((today + datetime.timedelta(days = i)).strftime("%Y%m%d"))
    #print(days)
    mp["days"] = days
    data = []
    for stu in students:
        records = r.lrange(f"clock_{stu}", 0, -1)
        record =  set(map(lambda x: x.decode('utf-8'), records))
        tmp = [stu]
        for day in days:
            tmp.append("已打卡" if day in record else "")
        if (cd := keep_day(tmp)) >= 3:
            tmp[0] += fr'<span class="label label-info">连续打卡{cd}天</span>'
        data.append(tmp)
    data.sort(key = lambda x: (x.count("已打卡"), keep_day(x)), reverse = True)
    mp["data"] = data
    return mp

if __name__ == '__main__':
    d = get_rank_data()
    print(d["days"])
    for line in d["data"]:
        print(line)
