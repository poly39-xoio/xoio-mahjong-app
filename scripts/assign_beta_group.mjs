// Assign the newest VALID build of the app to the internal TestFlight group.
// Runs in GitHub Actions right after "Upload to App Store Connect" so that new
// builds ALWAYS show up in TestFlight (prevents the "uploaded but invisible" miss).
// Env: ASC_KEY_ID, ASC_ISSUER_ID (required in CI). Key read from
//      $HOME/private_keys/AuthKey_<ASC_KEY_ID>.p8 (same path the workflow writes).
// Optional: ASC_KEY_PATH, ASC_APP_ID, ASC_BETA_GROUP, TARGET_BUILD (build number)
import fs from 'node:fs';
import crypto from 'node:crypto';

const KEY_ID = process.env.ASC_KEY_ID || '7MMR5Z7G34';
const ISSUER = process.env.ASC_ISSUER_ID || '19a86a9e-82a3-472f-a0b2-dc98b0e55819';
const KEY_PATH = process.env.ASC_KEY_PATH || `${process.env.HOME}/private_keys/AuthKey_${KEY_ID}.p8`;
const APP = process.env.ASC_APP_ID || '6811858851';
const GROUP = process.env.ASC_BETA_GROUP || 'e3fe0f03-029a-4e2e-af76-b9f41310ede4'; // Internal Testing

// 2026-10-10 FIX: MUST target THIS upload's build number.
// 舊 bug: 上傳後立刻查「最新 build」,但 Apple 註冊新 build 有數分鐘延遲,
//         當下最新仍是上一版(已在群組)→ 誤判 already-in-group 而跳過,新 build 永遠沒加入。
// 正解: 從 pbxproj 的 CURRENT_PROJECT_VERSION 讀出本次 build 號當目標。
function readBuildNumber() {
  for (const p of ['ios/App/App.xcodeproj/project.pbxproj']) {
    try {
      const m = fs.readFileSync(p, 'utf8').match(/CURRENT_PROJECT_VERSION = (\d+);/);
      if (m) return m[1];
    } catch (e) {}
  }
  return null;
}
const TARGET = process.env.TARGET_BUILD || readBuildNumber();
const API = 'https://api.appstoreconnect.apple.com';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const b64url = (b) => Buffer.from(b).toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
function token() {
  const now = Math.floor(Date.now() / 1000);
  const head = b64url(JSON.stringify({ alg: 'ES256', kid: KEY_ID, typ: 'JWT' }));
  const pay = b64url(JSON.stringify({ iss: ISSUER, iat: now, exp: now + 1200, aud: 'appstoreconnect-v1' }));
  const input = head + '.' + pay;
  const key = fs.readFileSync(KEY_PATH, 'utf8');
  const sig = crypto.sign('sha256', Buffer.from(input), { key, dsaEncoding: 'ieee-p1363' });
  return input + '.' + b64url(sig);
}
async function api(method, path, body) {
  const res = await fetch(API + path, {
    method,
    headers: { Authorization: 'Bearer ' + token(), ...(body ? { 'Content-Type': 'application/json' } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  let json = null; try { json = await res.json(); } catch (e) {}
  return { status: res.status, json };
}
async function pickBuild() {
  const { status, json } = await api('GET', `/v1/builds?filter[app]=${APP}&limit=12&sort=-uploadedDate&fields[builds]=version,processingState,uploadedDate`);
  if (status !== 200 || !json || !json.data) return null;
  if (TARGET) return json.data.find((b) => String(b.attributes.version) === String(TARGET)) || null; // data 已按 uploadedDate 新→舊,取最新符合者
  return json.data[0] || null;
}

(async () => {
  if (!TARGET) console.log('[assign] WARN: no TARGET build number (pbxproj/TARGET_BUILD) — falling back to latest');
  else console.log(`[assign] target build = ${TARGET}`);
  let build = null;
  for (let i = 0; i < 40; i++) {           // wait up to ~20 min for Apple to register+process THIS build
    build = await pickBuild();
    if (build && build.attributes.processingState === 'VALID') break;
    console.log(`[assign] waiting for build ${TARGET || '(latest)'} ... (${i + 1})` + (build ? ` state=${build.attributes.processingState}` : ' not found yet'));
    await sleep(30000);
  }
  if (!build || build.attributes.processingState !== 'VALID') { console.error('[assign] no VALID build found'); process.exit(1); }
  const bid = build.id, ver = build.attributes.version;

  await api('PATCH', `/v1/builds/${bid}`, { data: { type: 'builds', id: bid, attributes: { usesNonExemptEncryption: false } } });

  const g = await api('GET', `/v1/betaGroups/${GROUP}/builds?limit=100&fields[builds]=version`);
  const have = g.json && g.json.data ? g.json.data.map((b) => b.id) : [];
  if (have.includes(bid)) { console.log(`[assign] build ${ver} already in internal group`); return; }

  const r = await api('POST', `/v1/betaGroups/${GROUP}/relationships/builds`, { data: [{ type: 'builds', id: bid }] });
  if (![200, 201, 204].includes(r.status)) { console.error('[assign] failed', r.status, JSON.stringify(r.json)); process.exit(1); }

  // 驗證真的進群組(避免再次「回報成功但其實沒加」)
  const chk = await api('GET', `/v1/betaGroups/${GROUP}/builds?limit=200&fields[builds]=version`);
  const nowIds = chk.json && chk.json.data ? chk.json.data.map((b) => b.id) : [];
  if (!nowIds.includes(bid)) { console.error(`[assign] VERIFY FAILED: build ${ver} (${bid}) NOT in group after POST`); process.exit(1); }
  console.log(`[assign] build ${ver} (${bid}) assigned to internal TestFlight group — verified ✅`);
})();
