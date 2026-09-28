import sqlite3
c = sqlite3.connect("../signalprep_DEPLOY_CLEAN.db")
for t in ["user_answers", "test_questions", "test_attempts"]:
    c.execute(f"delete from {t}")
c.commit()
c.execute("vacuum")
print("integrity:", c.execute("pragma integrity_check").fetchone()[0])
for t in ["questions", "test_attempts", "test_questions", "user_answers", "test_configs"]:
    print(t, c.execute(f"select count(*) from {t}").fetchone()[0])
print(c.execute("select id, status from questions where id='supp-2026-s1-092'").fetchall())
print("questions columns:", [r[1] for r in c.execute("pragma table_info(questions)")])
print("profiles columns:", [r[1] for r in c.execute("pragma table_info(profiles)")])
