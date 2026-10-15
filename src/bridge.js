// Runs inside the web view before the reader loads. It replaces the browser's speech engine with one that
// forwards every sentence to the iPhone's own speech engine (expo-speech in App.js). Native speech uses the
// app's audio session, so the narrator goes to CarPlay, Bluetooth and the lock screen together with the music.
// The reader page itself is unchanged: it keeps calling speechSynthesis.speak() as it does in a browser.
export const BRIDGE_JS = `
(function () {
  if (!window.ReactNativeWebView) return;
  window.__UNDERTONE_NATIVE = true;
  var post = function (m) { window.ReactNativeWebView.postMessage(JSON.stringify(m)); };
  var pending = {}, count = 0, seq = 0, voices = [], listeners = {};

  function Utterance(text) {
    this.text = text || ''; this.rate = 1; this.pitch = 1; this.volume = 1; this.voice = null; this.lang = '';
    this.onend = null; this.onerror = null; this.onstart = null;
  }

  var synth = {
    speaking: false,
    pending: false,
    paused: false,
    getVoices: function () { return voices; },
    speak: function (u) {
      var id = ++seq; pending[id] = u; count++; synth.speaking = true;
      post({ type: 'speak', id: id, text: u.text, voice: u.voice ? u.voice.voiceURI : null,
             lang: u.voice ? u.voice.lang : (u.lang || null), rate: u.rate, pitch: u.pitch, volume: u.volume,
             session: 'app' });
    },
    cancel: function () {
      pending = {}; count = 0; synth.speaking = false;
      post({ type: 'stop' });
    },
    pause: function () {}, resume: function () {},
    addEventListener: function (t, f) { (listeners[t] = listeners[t] || []).push(f); },
    removeEventListener: function () {}
  };

  window.__native = {
    done: function (id) {
      var u = pending[id]; if (!u) return;
      delete pending[id]; count--; if (count <= 0) { count = 0; synth.speaking = false; }
      if (u.onend) u.onend({ type: 'end' });
    },
    error: function (id, msg) {
      var u = pending[id]; if (!u) return;
      delete pending[id]; count--; if (count <= 0) { count = 0; synth.speaking = false; }
      if (u.onerror) u.onerror({ type: 'error', error: msg || 'synthesis-failed' });
    },
    elevenState: function (hasKey, count, error) {
      if (typeof window.__elevenState === 'function') window.__elevenState(hasKey, count, error);
    },
    status: function (msg) {
      if (typeof window.__nativeStatus === 'function') window.__nativeStatus(msg);
    },
    voices: function (list) {
      voices = list || [];
      (listeners.voiceschanged || []).forEach(function (f) { try { f(); } catch (e) {} });
      if (typeof synth.onvoiceschanged === 'function') synth.onvoiceschanged();
    }
  };

  // The reader looks for these first. Overriding window.speechSynthesis itself isn't reliable in WebKit.
  window.__undertoneSynth = synth;
  window.__undertoneUtterance = Utterance;
  try { Object.defineProperty(window, 'speechSynthesis', { value: synth, configurable: true }); } catch (e) {}
  try { window.SpeechSynthesisUtterance = Utterance; } catch (e) {}
  post({ type: 'voices' });
})();
true;
`;
