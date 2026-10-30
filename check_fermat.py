import ssl, urllib.request, re
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
url = 'https://fermatslibrary.com/s/the-surprisingly-powerful-influence-of-drawing-on-memory'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
try:
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        print('Length:', len(html))
        matches = re.findall(r'href=[\'"]([^\'"]+\.pdf[^\'"]*)[\'"]', html, re.I)
        print('PDF links:', matches)
        matches2 = re.findall(r'[\'"]([^\'"]+pdf[^\'"]*)[\'"]', html, re.I)
        print('PDF string matches:', matches2[:5])
except Exception as e:
    print('Error:', e)
