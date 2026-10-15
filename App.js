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

// Play like a music or audiobook app: ignore the silent switch, keep going in the background,
// and follow the phone's audio output (CarPlay, Bluetooth, AirPlay) for both the voice and the music.
// Re-applied before every sentence: the web view's music can change or switch off the shared audio
// session (for example after a pause), and the narrator would then be silent.
function startAudioSession() {
  return configureAudio();
}
async function configureAudio() {
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

  useEffect(() => { startAudioSession(); }, []);

  const call = useCallback((fn, ...args) => {
    const js = `window.__native && window.__native.${fn}.apply(null, ${JSON.stringify(args)}); true;`;
    web.current?.injectJavaScript(js);
  }, []);

  const onMessage = useCallback(async (event) => {
    let m;
    try { m = JSON.parse(event.nativeEvent.data); } catch { return; }

    if (m.type === 'voices') {
      try {
        const list = await Speech.getAvailableVoicesAsync();
        call('voices', list.map(v => ({
          name: voiceLabel(v), lang: v.language, voiceURI: v.identifier, localService: true, default: false,
        })));
        call('status', `ready, ${list.length} voices found`);
      } catch (e) {
        call('status', `couldn't list voices (${e?.message || e})`);
      }
    } else if (m.type === 'speak') {
      const token = stopToken.current; // a later 'stop' makes this sentence stale
      const sessionError = await startAudioSession();
      if (stopToken.current !== token) return;
      if (sessionError) call('status', `audio setup failed (${sessionError})`);
      const speakWith = (voice, retried, session = m.session) => {
        let started = false;
        // If iPhone doesn't start speaking within a few seconds, the app's audio session is stuck:
        // stop and say the sentence through the iPhone speech system instead, so the narrator is never silent.
        const guard = session !== 'system' ? setTimeout(() => {
          if (started || stopToken.current !== token) return;
          Speech.stop();
          call('status', 'switched to the iPhone speech system for this sentence');
          speakWith(voice, retried, 'system');
        }, 2500) : null;
        try {
          Speech.speak(m.text, {
            voice: voice || undefined,
            language: voice ? undefined : (m.lang || undefined),
            rate: m.rate ?? 1,
            pitch: m.pitch ?? 1,
            volume: m.volume ?? 1,
            useApplicationAudioSession: session !== 'system',
            onStart: () => { started = true; clearTimeout(guard); call('status', `speaking (${session === 'system' ? 'iPhone speech system' : 'with the music'})`); },
            onDone: () => { clearTimeout(guard); if (stopToken.current === token) call('done', m.id); },
            onError: (err) => {
              clearTimeout(guard);
              // A voice that's been removed or isn't allowed fails here; fall back to the default voice once.
              if (voice && !retried) { speakWith(null, true); return; }
              call('status', `error: ${err?.message || err}`);
              call('error', m.id, String(err?.message || err));
            },
          });
        } catch (err) {
          clearTimeout(guard);
          if (voice && !retried) { speakWith(null, true); return; }
          call('status', `error: ${err?.message || err}`);
          call('error', m.id, String(err?.message || err));
        }
      };
      speakWith(m.voice, false);
    } else if (m.type === 'stop') {
      stopToken.current++;
      Speech.stop();
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
