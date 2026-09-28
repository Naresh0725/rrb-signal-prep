import sqlite3, os
for p in ["../signalprep.db", "./signalprep.db"]:
    print("==", os.path.abspath(p), os.path.getsize(p), "bytes")
    c = sqlite3.connect(p)
    for (t,) in c.execute("select name from sqlite_master where type='table' order by 1").fetchall():
        print("  ", t, c.execute(f'select count(*) from "{t}"').fetchone()[0])
