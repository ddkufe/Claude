# Undertone

An iPhone app that reads your PDF, EPUB and text books aloud, with background music that changes with the mood of each passage.

The reader itself (`reader/undertone.html`) is the same page as the web version. The app wraps it so that:

- the narrator uses the iPhone's own speech engine, including Premium and Enhanced voices you've downloaded;
- the narrator and the music share the app's audio session, so both play through CarPlay, Bluetooth and AirPlay;
- the music keeps playing with the silent switch on.

## Try it on your iPhone (Expo Go, no computer)

Every push to the `undertone-app` branch publishes the app to Expo (see `.github/workflows/publish-expo-go.yml`).

One-time setup:
1. Create a free account at expo.dev and install **Expo Go** from the App Store.
2. On expo.dev, open Account settings › Access tokens and create a token.
3. On GitHub, open this repository's Settings › Secrets and variables › Actions and add a secret named `EXPO_TOKEN` with that token.

Then sign in to Expo Go with the same account. The app appears there after each publish.

## Try it from a computer

1. Install **Expo Go** from the App Store.
2. On a computer with Node.js installed:
   ```bash
   git clone -b undertone-app https://github.com/ddkufe/Claude.git undertone
   cd undertone
   npm install
   npx expo start --tunnel
   ```
3. Scan the QR code with the iPhone camera. It opens in Expo Go.

## Install it as your own app

Needs an Apple Developer account ($99/year). Builds run in the cloud with EAS, so no Mac is needed:

```bash
npx eas-cli@latest build --platform ios --profile production
npx eas-cli@latest submit --platform ios
```

Then install it from TestFlight.

## Changing the reader

Edit `reader/undertone.html`, then run `npm run build:reader` to regenerate `src/readerHtml.js`.

## How the pieces fit

- `App.js` sets the audio session (playback, background, ignore the silent switch), shows the reader in a web view, and speaks each sentence the reader sends it with `expo-speech`.
- `src/bridge.js` runs inside the web view and stands in for the browser's `speechSynthesis`, forwarding speech to the app.
- `reader/undertone.html` is the reader: file opening, mood detection, generated music, library and settings.
