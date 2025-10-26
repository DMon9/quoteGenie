# Very simple feedback hook: append corrections to a local file / table.

import json
from datetime import datetime

FEEDBACK_FILE = 'feedback_log.jsonl'

def save_feedback(quote_id: str, corrections: str):
    entry = {
        'quote_id': quote_id,
        'corrections': corrections,
        'timestamp': datetime.utcnow().isoformat()
    }
    with open(FEEDBACK_FILE, 'a') as f:
        f.write(json.dumps(entry) + "\n")
    return True
