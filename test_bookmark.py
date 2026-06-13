import urllib.request, json

# Login
data = json.dumps({'email': 'researcher1@example.com', 'password': 'password123'}).encode()
req = urllib.request.Request('http://localhost:8000/api/auth/login', data=data, headers={'Content-Type': 'application/json'}, method='POST')
resp = urllib.request.urlopen(req)
login_result = json.load(resp)
token = login_result['access_token']
print(f"Login successful, token: {token[:20]}...")

# Test bookmark creation
data = json.dumps({'paper_id': 1}).encode()
req = urllib.request.Request('http://localhost:8000/api/social/bookmarks', data=data, headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}, method='POST')
resp = urllib.request.urlopen(req)
bookmark_result = json.load(resp)
print(f"Bookmark result: {bookmark_result}")

# Test getting bookmarks
req = urllib.request.Request('http://localhost:8000/api/social/bookmarks', headers={'Authorization': f'Bearer {token}'}, method='GET')
resp = urllib.request.urlopen(req)
bookmarks = json.load(resp)
print(f"Bookmarks count: {len(bookmarks)}")
if bookmarks:
    print(f"First bookmark paper: {bookmarks[0].get('paper', {}).get('title', 'No paper data')}")