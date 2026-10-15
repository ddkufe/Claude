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
    } else if (m.type === 'voices' || m.type === 'elevenKey') {
      if (m.type === 'elevenKey') {
        try { await Eleven.saveKey(m.key); } catch (e) { call('status', `couldn't save the key (${e?.message || e})`); return; }
      } else await Eleven.loadKey();
      let list = [];
      try {
        list = (await Speech.getAvailableVoicesAsync()).map(v => ({
          name: voiceLabel(v), lang: v.language, voiceURI: v.identifier, localService: true, default: false,
        }));
      } catch (e) {
        call('status', `couldn't list voices (${e?.message || e})`);
      }
      let eleven = [], elevenError = null;
      try { eleven = await Eleven.listVoices(); } catch (e) { elevenError = e?.message || String(e); }
      call('voices', [...eleven, ...list]);
      call('elevenState', Eleven.hasKey(), eleven.length, elevenError);
      call('status', elevenError ? elevenError
        : `ready, ${list.length} iPhone voices${Eleven.hasKey() ? ` and ${eleven.length} ElevenLabs voices` : ''}`);
    } else if (m.type === 'prefetch') {
      // Ask ElevenLabs for the next sentences while this one plays, so there's no gap between them.
      for (const t of m.items || []) {
        if (t.voice?.startsWith(Eleven.PREFIX) && Eleven.hasKey()) Eleven.audioFor(t.voice.slice(Eleven.PREFIX.length), t.text, t.rate).catch(() => {});
      }
    } else if (m.type === 'speak') {
      const token = stopToken.current; // a later 'stop' makes this sentence stale
      try { await setIsAudioActiveAsync(true); } catch {}
      if (stopToken.current !== token) return;
      if (m.voice?.startsWith(Eleven.PREFIX)) {
        if (Eleven.hasKey()) {
          try {
            const finished = await Eleven.speak(m.voice.slice(Eleven.PREFIX.length), m.text, m.rate, () => call('status', 'speaking with ElevenLabs'));
            if (finished && stopToken.current === token) call('done', m.id);
            return;
          } catch (e) {
            if (stopToken.current !== token) return;
            call('status', `${e?.message || e}, using the iPhone voice for now`);
          }
        }
        m.voice = null; // no key, or ElevenLabs failed: read this sentence with the iPhone's default voice
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
      Eleven.stop();
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
