import json
from pathlib import Path

project = Path(r"C:\Users\mamil\OneDrive\Desktop\rrb-signal-mock-updated")
batch = Path(r"C:\Users\mamil\Downloads\SignalPrep_Batch_03_Science_Engineering\backend\data\preparation_batch_03.json")
bank = project / "backend\data\preparation_questions.json"

old = json.loads(bank.read_text(encoding="utf-8"))
new = json.loads(batch.read_text(encoding="utf-8"))

old_ids = {x["id"] for x in old}
new_ids = [x["id"] for x in new]
collisions = old_ids.intersection(new_ids)

assert not collisions, f"ID COLLISIONS: {sorted(collisions)}"
assert len(new) == 20, f"Expected 20, got {len(new)}"

merged = old + new

bank.write_text(
    json.dumps(merged, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print(f"OLD: {len(old)}")
print(f"ADDED: {len(new)}")
print(f"NEW TOTAL: {len(merged)}")
print(f"NEW UNIQUE IDs: {len({x['id'] for x in merged})}")
