#!/usr/bin/env python3
import subprocess, json, urllib.request, os, zipfile, shutil, time

repo = 'poly39-xoio/xoio-mahjong-app'
os.chdir('/root/.openclaw/workspace/xoio-mahjong-app')
url = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], universal_newlines=True).strip()
tok = url.split('//', 1)[1].split('@', 1)[0].split(':', 1)[1]

def api(p):
    req = urllib.request.Request('https://api.github.com/repos/' + repo + p, headers={
        'Authorization': 'token ' + tok, 'Accept': 'application/vnd.github+json', 'User-Agent': 'io'})
    return json.load(urllib.request.urlopen(req, timeout=60))

def dl(p, dest):
    subprocess.check_call(['curl', '-sL', '-o', dest,
        '-H', 'Authorization: token ' + tok,
        '-H', 'Accept: application/vnd.github+json',
        'https://api.github.com/repos/' + repo + p])

r = None
for i in range(50):
    runs = api('/actions/runs?per_page=10')['workflow_runs']
    mine = [x for x in runs if x['name'] == 'Android release AAB']
    if mine:
        r = mine[0]
        print('[%d] %s %s %s' % (i, r['status'], r['conclusion'], r['head_sha'][:7]), flush=True)
        if r['status'] == 'completed':
            break
    else:
        print('[%d] (run 尚未出現)' % i, flush=True)
    time.sleep(30)

if not r or r['status'] != 'completed':
    raise SystemExit('timeout')
if r['conclusion'] != 'success':
    raise SystemExit('release run 失敗: ' + str(r['conclusion']))

arts = api('/actions/runs/%d/artifacts' % r['id'])['artifacts']
print('artifacts:', [(a['name'], round(a['size_in_bytes']/1048576, 2)) for a in arts], flush=True)
aid = [a for a in arts if a['name'] == 'mahjong-release-aab'][0]['id']
dl('/actions/artifacts/%d/zip' % aid, '/tmp/aab.zip')
shutil.rmtree('/tmp/aab', ignore_errors=True)
with zipfile.ZipFile('/tmp/aab.zip') as zf:
    print('zip:', zf.namelist(), flush=True)
    zf.extractall('/tmp/aab')
aab = [os.path.join('/tmp/aab', f) for f in os.listdir('/tmp/aab') if f.endswith('.aab')][0]
print('AAB:', aab, os.path.getsize(aab), 'bytes', flush=True)

pw = open('/root/android-keys/keystore-password.txt').read().strip()
subprocess.check_call(['jarsigner', '-keystore', '/root/android-keys/mahjong-release.jks',
    '-storepass', pw, '-keypass', pw, '-sigalg', 'SHA256withRSA', '-digestalg', 'SHA-256', aab, 'mahjong'])
print('已簽章', flush=True)
v = subprocess.run(['jarsigner', '-verify', '-verbose', aab], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
print(v.stdout[-600:], flush=True)

dl_dir = '/var/www/hashguess-game/s/' + open('.dl_token').read().strip()
out = os.path.join(dl_dir, 'mahjong-release.aab')
shutil.copy(aab, out)
print('-> ' + out, os.path.getsize(out), 'bytes', flush=True)
