import sqlite3
c = sqlite3.connect("file:../signalprep.db?mode=ro", uri=True)
c.row_factory = sqlite3.Row
def show(sql):
    print("--", sql)
    for r in c.execute(sql):
        print({k: (str(r[k])[:70]) for k in r.keys()})
show("select id, mode, status from test_attempts")
show("select * from test_configs where id='supplementary'")
show("select source_type, status, count(*) n from questions group by 1,2")
show("select subject, count(*) n from questions where source_type='SUPPLEMENTARY' group by 1")
