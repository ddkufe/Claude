import { createAudioPlayer } from 'expo-audio';
import { File, Directory, Paths } from 'expo-file-system';
import * as SecureStore from 'expo-secure-store';

// ElevenLabs voices, using the reader's own ElevenLabs API key (kept in the iPhone keychain, never in the app's code).
// Each sentence is turned into an MP3 by ElevenLabs and played with the app's audio player, in the same
// audio session as the music, so it reaches CarPlay and Bluetooth the same way.
const API = 'https://api.elevenlabs.io/v1';
const KEY_NAME = 'elevenlabs-api-key';
const MODEL = 'eleven_multilingual_v2';
export const PREFIX = 'eleven:';

let apiKey = null;
const dir = new Directory(Paths.cache, 'eleven');
const pending = new Map(); // cache file name -> Promise<File>

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

async function api(path, init = {}) {
  const res = await fetch(API + path, { ...init, headers: { 'xi-api-key': apiKey, ...(init.headers || {}) } });
  if (!res.ok) {
    let detail = '';
    try { const j = await res.json(); detail = j?.detail?.message || j?.detail?.status || JSON.stringify(j?.detail || j); } catch {}
    throw new Error(res.status === 401 ? 'ElevenLabs didn\'t accept the key' : `ElevenLabs error ${res.status}${detail ? ': ' + detail : ''}`);
  }
  return res;
}

// The voices in the reader's ElevenLabs account, shaped like the phone's voices for the reader's voice picker.
export async function listVoices() {
  if (!apiKey) return [];
  const j = await (await api('/voices')).json();
  return (j.voices || []).map(v => ({
    name: `${v.name} (ElevenLabs)`, lang: 'en-US', voiceURI: PREFIX + v.voice_id, localService: false, default: false,
  }));
}

function hash(s) { let h = 2166136261; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0).toString(36); }

// Fetch (or reuse) the MP3 for one sentence. Sentences are cached, so replaying or going back costs nothing.
export function audioFor(voiceId, text, speed) {
  const s = Math.min(1.2, Math.max(0.7, speed || 1)).toFixed(2);
  const name = `${voiceId}-${s}-${hash(text)}-${text.length}.mp3`;
  if (pending.has(name)) return pending.get(name);
  const p = (async () => {
    if (!dir.exists) dir.create({ intermediates: true });
    const f = new File(dir, name);
    if (f.exists && f.size > 0) return f;
    const res = await api(`/text-to-speech/${voiceId}?output_format=mp3_44100_128`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'audio/mpeg' },
      body: JSON.stringify({ text, model_id: MODEL, voice_settings: { stability: 0.45, similarity_boost: 0.8, speed: +s } }),
    });
    const bytes = new Uint8Array(await res.arrayBuffer());
    if (f.exists) f.delete();
    f.create();
    f.write(bytes);
    return f;
  })();
  pending.set(name, p);
  p.catch(() => {}).finally(() => { if (pending.get(name) === p) pending.delete(name); });
  return p;
}

let current = null;
export function stop() {
  if (current) { try { current.remove(); } catch {} current = null; }
}
// Play one sentence; resolves when it has finished.
export async function speak(voiceId, text, speed, onStart) {
  const f = await audioFor(voiceId, text, speed);
  stop();
  return new Promise((resolve) => {
    const player = createAudioPlayer({ uri: f.uri });
    current = player;
    let started = false;
    player.addListener('playbackStatusUpdate', (st) => {
      if (!started && st.playing) { started = true; onStart?.(); }
      if (st.didJustFinish) { if (current === player) stop(); resolve(true); }
    });
    // A stop() before the end removes the player; settle so nothing waits forever.
    const check = setInterval(() => { if (current !== player) { clearInterval(check); resolve(false); } }, 250);
    player.play();
  });
}
