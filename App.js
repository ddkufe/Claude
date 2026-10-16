import { useCallback, useEffect, useRef } from 'react';
import { StyleSheet, useColorScheme } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { WebView } from 'react-native-webview';
import * as Speech from 'expo-speech';
import { setAudioModeAsync, setIsAudioActiveAsync } from 'expo-audio';
import { useKeepAwake } from 'expo-keep-awake';
import { READER_HTML } from './src/readerHtml';
import { BRIDGE_JS } from './src/bridge';
import { createMusic } from './src/music';
import * as Eleven from './src/eleven';
import * as Speechify from './src/speechify';

// Online voices the reader can add with their own API key. Their voices show up in the reader's list as '<prefix><id>'.
const CLOUD = [
  { svc: Eleven, name: 'ElevenLabs', keyMsg: 'elevenKey', state: 'elevenState' },
  { svc: Speechify, name: 'Speechify', keyMsg: 'speechifyKey', state: 'speechifyState' },
];
const cloudFor = (voice) => CLOUD.find(c => voice?.startsWith(c.svc.PREFIX));

// Play like a music or audiobook app: ignore the silent switch, keep going in the background,
// and follow the phone's audio output (CarPlay, Bluetooth, AirPlay) for both the voice and the music.
// The voice (expo-speech) and the music (expo-audio players) both live in this one session; the web view
// makes no sound at all, so nothing else can take the session over.
async function startAudioSession() {
  try {
    await setAudioModeAsync({
      playsInSilentMode: true,
      shouldPlayInBackground: true,
      interruptionMode: 'doNotMix',
      allowsRecording: false,
    });
    await setIsAudioActiveAsync(true);
    return null;
  } catch (e) {
    console.warn('Could not set audio mode', e);
    return String(e?.message || e);
  }
}

// Premium and Enhanced voices sound far better than the defaults; put that in the name so the
// reader's voice picker can rank them.
function voiceLabel(v) {
  const id = (v.identifier || '').toLowerCase();
  if (id.includes('premium')) return `${v.name} (Premium)`;
  if (v.quality === 'Enhanced' || id.includes('enhanced')) return `${v.name} (Enhanced)`;
  return v.name;
}

export default function App() {
  useKeepAwake();
  const web = useRef(null);
  const stopToken = useRef(0);
  const dark = useColorScheme() === 'dark';
  const music = useRef(null);

  useEffect(() => { startAudioSession(); }, []);

  const call = useCallback((fn, ...args) => {
    const js = `window.__native && window.__native.${fn}.apply(null, ${JSON.stringify(args)}); true;`;
    web.current?.injectJavaScript(js);
  }, []);

  if (!music.current) {
    music.current = createMusic({
      requestRender: (mood) => web.current?.injectJavaScript(`window.__undertoneRenderMusic && window.__undertoneRenderMusic(${JSON.stringify(mood)}); true;`),
      status: (msg) => call('status', msg),
    });
  }

  const onMessage = useCallback(async (event) => {
    let m;
    try { m = JSON.parse(event.nativeEvent.data); } catch { return; }

    if (m.type === 'music') {
      const mu = music.current;
      if (m.op === 'start') { await startAudioSession(); mu.start(m.vol); }
      else if (m.op === 'pause') mu.pause();
      else if (m.op === 'volume') mu.volume(m.vol);
      else if (m.op === 'mood') mu.mood(m.mood);
      else if (m.op === 'data') mu.data(m.mood, m.data);
    } else if (m.type === 'voices' || CLOUD.some(c => c.keyMsg === m.type)) {
      const keyed = CLOUD.find(c => c.keyMsg === m.type);
      if (keyed) {
        try { await keyed.svc.saveKey(m.key); } catch (e) { call('status', `couldn't save the key (${e?.message || e})`); return; }
      }
      for (const c of CLOUD) if (c !== keyed) await c.svc.loadKey();
      let list = [];
      try {
        list = (await Speech.getAvailableVoicesAsync()).map(v => ({
          name: voiceLabel(v), lang: v.language, voiceURI: v.identifier, localService: true, default: false,
        }));
      } catch (e) {
        call('status', `couldn't list voices (${e?.message || e})`);
      }
      const online = [], notes = [];
      for (const c of CLOUD) {
        let vs = [], err = null;
        try { vs = await c.svc.listVoices(); } catch (e) { err = e?.message || String(e); }
        online.push(...vs);
        call(c.state, c.svc.hasKey(), vs.length, err, c.svc.usage ? await c.svc.usage() : null);
        notes.push(err || (c.svc.hasKey() ? `${vs.length} ${c.name} voices` : ''));
      }
      call('voices', [...online, ...list]);
      call('status', [`ready, ${list.length} iPhone voices`, ...notes.filter(Boolean)].join(', '));
    } else if (m.type === 'prefetch') {
      // Ask the online voice for the next sentences while this one plays, so there's no gap between them.
      for (const t of m.items || []) {
        const c = cloudFor(t.voice);
        if (c && c.svc.hasKey()) c.svc.audioFor(t.voice.slice(c.svc.PREFIX.length), t.text, t.rate).catch(() => {});
      }
    } else if (m.type === 'speak') {
      const token = stopToken.current; // a later 'stop' makes this sentence stale
      try { await setIsAudioActiveAsync(true); } catch {}
      if (stopToken.current !== token) return;
      const c = cloudFor(m.voice);
      if (c) {
        let problem = { message: `no ${c.name} key saved`, lasting: true };
        if (c.svc.hasKey()) {
          // One retry for a passing problem (weak signal in the car, a busy server) before giving up on this sentence.
          for (let attempt = 0; attempt < 2; attempt++) {
            try {
              const finished = await c.svc.speak(m.voice.slice(c.svc.PREFIX.length), m.text, m.rate, () => call('status', `speaking with ${c.name}`));
              if (finished && stopToken.current === token) call('done', m.id);
              return;
            } catch (e) {
              if (stopToken.current !== token) return;
              problem = { message: e?.message || String(e), lasting: !!e?.lasting };
              if (problem.lasting) break;
            }
          }
        }
        // Tell the reader why, so it can say so on screen, then read this sentence with the reader's best iPhone voice.
        call('voiceProblem', m.voice, problem.message, problem.lasting);
        if (problem.lasting && c.svc.hasKey() && c.svc.usage) c.svc.usage().then(u => call(c.state, true, null, null, u));
        call('status', `${problem.message}, using the iPhone voice for now`);
        m.voice = m.fallback || null;
      }
      const speakWith = (voice, retried) => {
        let started = false;
        // Always speak in the app's own audio session, the same one the music plays in, so the voice
        // follows CarPlay and Bluetooth with it. Never fall back to the iPhone speech system: that one
        // plays on the phone's speaker even when the car is connected.
        const slow = setTimeout(() => { if (!started && stopToken.current === token) call('status', 'waiting for the voice to start…'); }, 4000);
        const fail = (err) => {
          clearTimeout(slow);
          // A voice that's been removed or isn't allowed fails here; fall back to the default voice once.
          if (voice && !retried) { speakWith(null, true); return; }
          call('status', `error: ${err?.message || err}`);
          call('error', m.id, String(err?.message || err));
        };
        try {
          Speech.speak(m.text, {
            voice: voice || undefined,
            language: voice ? undefined : (m.lang || undefined),
            rate: m.rate ?? 1,
            pitch: m.pitch ?? 1,
            volume: m.volume ?? 1,
            useApplicationAudioSession: true,
            onStart: () => { started = true; clearTimeout(slow); call('status', 'speaking with the music'); },
            onDone: () => { clearTimeout(slow); if (stopToken.current === token) call('done', m.id); },
            onError: fail,
          });
        } catch (err) { fail(err); }
      };
      speakWith(m.voice, false);
    } else if (m.type === 'stop') {
      stopToken.current++;
      Speech.stop();
      Eleven.stop(); // the same player stops Speechify too
    }
  }, [call]);

  return (
    <SafeAreaProvider>
      <SafeAreaView style={[styles.root, { backgroundColor: dark ? '#0e1115' : '#eceef1' }]} edges={['top', 'left', 'right']}>
        <StatusBar style={dark ? 'light' : 'dark'} />
        <WebView
          ref={web}
          style={styles.web}
          originWhitelist={['*']}
          source={{ html: READER_HTML, baseUrl: 'https://undertone.app/' }}
          injectedJavaScriptBeforeContentLoaded={BRIDGE_JS}
          onMessage={onMessage}
          // If iPhone stops the page to free memory (for example while importing a very long book), bring it back;
          // the import was saved as it went and continues when the same file is opened again.
          onContentProcessDidTerminate={() => web.current?.reload()}
          javaScriptEnabled
          domStorageEnabled
          allowsInlineMediaPlayback
          mediaPlaybackRequiresUserAction={false}
          allowFileAccess
          allowsBackForwardNavigationGestures={false}
          setSupportMultipleWindows={false}
          onShouldStartLoadWithRequest={(req) => req.url.startsWith('https://undertone.app') || req.url === 'about:blank' || req.url.startsWith('data:') || req.url.startsWith('blob:')}
        />
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  web: { flex: 1, backgroundColor: 'transparent' },
});
