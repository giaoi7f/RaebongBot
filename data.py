import sqlite3
import datetime

con = sqlite3.connect("userdata.db")
c = con.cursor()


week = ['월', '화', '수', '목', '금', '토', '일']
weekday = datetime.datetime.today().weekday() + 1
week = week[weekday:]+week[:weekday]
print(week)
