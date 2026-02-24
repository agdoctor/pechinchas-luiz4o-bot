import asyncio, re, sys
from unittest.mock import Mock
import database
database.get_config = lambda x: 'test'
from web_dashboard import handle_index

req = Mock()
req.query = {'token':'test'}
res = asyncio.run(handle_index(req))

js = re.search(r'<script>(.*?)</script>', res.text, re.DOTALL)
if js:
    with open('eval.js', 'w', encoding='utf-8') as f:
        f.write(js.group(1))
    print("JS extracted. Run 'node -c eval.js'.")
else:
    print("No script tag found!")
    sys.exit(1)
