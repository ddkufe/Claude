import * as Player from './voicePlayer';
import { File, Directory, Paths } from 'expo-file-system';
import * as SecureStore from 'expo-secure-store';

// Speechify voices, using the reader's own Speechify API key (kept in the iPhone keychain, never in the app's code).
// Each sentence comes back from Speechify as an MP3 and plays through the app's audio player, like ElevenLabs.
const API = 'https://api.speechify.ai/v1';
const VERSION = '2026-09-13';
const KEY_NAME = 'speechify-api-key';
export const PREFIX = 'speechify:';

let apiKey = null;
const dir = new Directory(Paths.cache, 'speechify');
const pending = new Map(); // cache file name -> Promise<File>
const models = new Map(); // voice id -> the model to read it with

export async function loadKey() {
  try { apiKey = await SecureStore.getItemAsync(KEY_NAME); } catch { apiKey = null; }
  return !!apiKey;
}
export async function saveKey(key) {
  apiKey = (key || '').trim() || null;
  if (apiKey) await SecureStore.setItemAsync(KEY_NAME, apiKey);
  else await SecureStore.deleteItemAsync(KEY_NAME);
}
export const hasKey = () => !!apiKey;

// Speechify's errors, in words the reader understands. `lasting` means retrying won't help.
function explain(status, body) {
  const text = String(body?.message || body?.detail?.message || body?.detail || body?.error || '').trim().replace(/\.$/, '');
  const says = text ? ` (Speechify says: ${text})` : '';
  const err = (message, lasting) => Object.assign(new Error(message), { lasting, status });
  if (status === 401) return err('Speechify didn\'t accept the key' + says, true);
  if (status === 402 || /credit|quota|limit|balance|plan/i.test(text)) return err('your Speechify account is out of characters or needs a paid plan' + says, true);
  if (status === 403) return err('this Speechify key isn\'t allowed to do that' + says, true);
  if (status === 404) return err('Speechify couldn\'t find this voice' + says, true);
  if (status === 429) return err('Speechify is busy right now', false);
  return err(`Speechify error ${status}${says}`, status >= 400 && status < 500);
}

async function api(path, init = {}) {
  let res;
  const ac = new AbortController(), t = setTimeout(() => ac.abort(), 20000); // a dropped signal in the car shouldn't hang the book
  try {
    res = await fetch(API + path, { ...init, signal: ac.signal,
      headers: { Authorization: `Bearer ${apiKey}`, 'Speechify-Version': VERSION, Accept: 'application/json', ...(init.headers || {}) } });
  } catch { throw Object.assign(new Error('couldn\'t reach Speechify (no internet?)'), { lasting: false }); }
  finally { clearTimeout(t); }
  if (!res.ok) {
    let body = null;
    try { body = await res.json(); } catch {}
    throw explain(res.status, body);
  }
  return res;
}

// Speechify's newest English model sounds best; other languages need the multilingual one.
function pickModel(v) {
  const names = (v.models || []).map(m => m.name);
  const english = /^en/i.test(v.locale || '');
  for (const n of english ? ['simba-3.2', 'simba-3.0', 'simba-english'] : ['simba-3.0', 'simba-multilingual']) if (names.includes(n)) return n;
  return names[0] || undefined;
}

// The voices the reader's Speechify key can use, shaped like the phone's voices for the reader's voice picker.
export async function listVoices() {
  if (!apiKey) return [];
  const j = await (await api('/voices')).json();
  const list = Array.isArray(j) ? j : (j.voices || []);
  return list.map(v => {
    models.set(v.id, pickModel(v));
    return { name: `${v.display_name || v.id} (Speechify)`, lang: (v.locale || 'en-US').replace('_', '-'), voiceURI: PREFIX + v.id, localService: false, default: false };
  });
}

function hash(s) { let h = 2166136261; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0).toString(36); }

// Fetch (or reuse) the MP3 for one sentence. Sentences are cached, so replaying or going back costs nothing.
export function audioFor(voiceId, text) {
  const name = `${voiceId.replace(/[^\w-]/g, '_')}-${hash(text)}-${text.length}.mp3`;
  if (pending.has(name)) return pending.get(name);
  const p = (async () => {
    if (!dir.exists) dir.create({ intermediates: true });
    const f = new File(dir, name);
    if (f.exists && f.size > 0) return f;
    const res = await api('/audio/speech', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input: text, voice_id: voiceId, audio_format: 'mp3', model: models.get(voiceId),
        options: { loudness_normalization: true, text_normalization: true } }),
    });
    const j = await res.json();
    if (!j.audio_data) throw Object.assign(new Error('Speechify sent no audio'), { lasting: false });
    if (f.exists) f.delete();
    f.create();
    f.write(j.audio_data, { encoding: 'base64' });
    return f;
  })();
  pending.set(name, p);
  p.catch(() => {}).finally(() => { if (pending.get(name) === p) pending.delete(name); });
  return p;
}

export const stop = Player.stop;
// Play one sentence; resolves when it has finished. Speechify has no speed setting, so the player sets the pace.
export async function speak(voiceId, text, speed, onStart) {
  const f = await audioFor(voiceId, text);
  return Player.play(f, speed || 1, onStart);
}
