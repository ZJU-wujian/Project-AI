"""Update journal volume and issue numbers to latest verified values."""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models.journal import Journal

updates = {
    'Nature': {'volume': 654, 'issue': 8118},
    'Science': {'volume': 392, 'issue': 6801},
    'Cell': {'volume': 189, 'issue': 8},
    'The Lancet': {'volume': 407, 'issue': 10545},
    'Nature Neuroscience': {'volume': 29, 'issue': 5},
    'Nature Biotechnology': {'volume': 44, 'issue': 5},
}

db = SessionLocal()
print('Updating journal volume/issue data:')
for name, data in updates.items():
    j = db.query(Journal).filter(Journal.name == name).first()
    if j:
        print(f'  {name}: Vol {j.volume} -> {data["volume"]}, Issue {j.issue} -> {data["issue"]}')
        j.volume = data['volume']
        j.issue = data['issue']
    else:
        print(f'  SKIP: {name} not found')
db.commit()
db.close()
print('Update complete!')
