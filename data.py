import sqlite3

con = sqlite3.connect("userdata.db")
c = con.cursor()

for data in c.execute(f"SELECT * FROM userdata").fetchall():
    c.execute(f"UPDATE userdata SET history='{'-'.join(data[2].split('-')[1:] + ['0'])}' WHERE id={data[0]}")
con.commit()
