#!/usr/bin/env python3
import subprocess, json, urllib.request, os, zipfile, shutil, time

repo = 'poly39-xoio/xoio-mahjong-app'
os.chdir('/root/.openclaw/workspace/xoio-mahjong-app')

url = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], universal_newlines=True).strip()
creds = url.split('//', 1)[1].split('@', 1)[0]
tok = creds.split(':', 1)[1]

def api_get(path):
    req = urllib.request.Request('https://api.github.com/repos/' + repo + path, headers={
        'Authorization': 'token ' + tok,
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'io-ci',
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def api_dl(path, dest):
    subprocess.check_call(['curl', '-sL', '-o', dest,
        '-H', 'Authorization: token ' + tok,
        '-H', 'Accept: application/vnd.github+json',
        'https://api.github.com/repos/' + repo + path])

for i in range(40):
    runs = api_get('/actions/runs?per_page=5')['workflow_runs']
    st = ' | '.join("%s=%s/%s" % (r['name'][:22], r['status'], r['conclusion']) for r in runs)
    print('[%d] %s' % (i, st), flush=True)
    if all(r['status'] == 'completed' for r in runs[:2]):
        break
    time.sleep(40)

runs = api_get('/actions/runs?per_page=5')['workflow_runs']
ios = [r for r in runs if 'iOS' in r['name']][0]
print('iOS run:', ios['id'], ios['conclusion'], ios['head_sha'][:7])
arts = api_get("/actions/runs/%d/artifacts" % ios['id'])['artifacts']
for a in arts:
    print('  art', a['id'], a['name'], round(a['size_in_bytes'] / 1048576, 2), 'MB')

dl_dir = '/var/www/hashguess-game/s/' + open('.dl_token').read().strip()
os.makedirs(dl_dir, exist_ok=True)
for a in arts:
    z = '/tmp/art-%d.zip' % a['id']
    ex = '/tmp/art-%d' % a['id']
    api_dl("/actions/artifacts/%d/zip" % a['id'], z)
    shutil.rmtree(ex, ignore_errors=True)
    with zipfile.ZipFile(z) as zf:
        print(' zip:', zf.namelist())
        zf.extractall(ex)
    for root, _, files in os.walk(ex):
        for fn in files:
            p = os.path.join(root, fn)
            if a['name'] == 'mahjong-ios-ipa' and fn.endswith('.ipa'):
                shutil.copy(p, os.path.join(dl_dir, 'xoio-mahjong-ios.ipa'))
                print('  -> xoio-mahjong-ios.ipa')
            if a['name'] == 'mahjong-ios-xcode-project' and fn.endswith('.zip'):
                shutil.copy(p, os.path.join(dl_dir, 'mahjong-xcode-project.zip'))
                shutil.copy(p, os.path.join(dl_dir, 'mahjong-xcode-project-fixed.zip'))
                print('  -> mahjong-xcode-project.zip + -fixed.zip')

print('=== dl dir ===')
for fn in sorted(os.listdir(dl_dir)):
    print(' ', fn, os.path.getsize(os.path.join(dl_dir, fn)), 'bytes')
