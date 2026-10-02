# Installing Live Actions

Windows only. About five minutes.

## 1. Check what you have

| Need | How to check |
|---|---|
| Ableton Live 12 with Max for Live | In Live, the browser shows a **Max for Live** category. Live Suite includes it; Standard needs the add-on. |
| Python 3.10+ | Open PowerShell and run `py -3 --version`. If that fails, install Python 3.12 from [python.org](https://www.python.org/downloads/) and tick **Add python.exe to PATH**. |
| WebView2 Runtime | Usually already installed. The installer tells you if it is missing; get the Evergreen runtime from [microsoft.com/edge/webview2](https://developer.microsoft.com/microsoft-edge/webview2/). |
| ffmpeg (optional) | Only for the Audio Sample and TTS Vocal tools. |

## 2. Get the files

```powershell
git clone https://github.com/mkomorny/live-actions.git
```

Or download the ZIP from the repository page and unzip it. Put the folder somewhere permanent:
the Desktop shortcut and the device both point at it.

## 3. Run the installer

In PowerShell, inside the folder:

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

It will:

1. Create `.venv` in the folder and install the Python packages into it.
2. Find your Ableton User Library and copy the **Live Actions** device into
   `Presets\Audio Effects\Max Audio Effect\Live Actions`.
3. Copy the optional browser Remote Script into `Remote Scripts\LiveActionsRS`.
4. Check that the knowledge database is in place.
5. Add a **Live Actions** shortcut to the Desktop and register the `liveactions://` link that the
   device's **Open desktop host** button uses.

It does not need admin rights, and it does not ask for an API key.

If it cannot find your User Library, it asks for the path. In Live this is under
**Settings → Library → Location of User Library**. You can also pass it directly:

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1 -UserLibrary "D:\Music\Ableton\User Library"
```

Other switches: `-NoShortcut`, `-NoProtocol`, `-SkipPackages`.

## 4. First run

1. Start (or restart) Live.
2. In Live's browser open **User Library → Presets → Audio Effects → Max Audio Effect** and drag
   **Live Actions** onto any track.
3. Double-click **Live Actions** on the Desktop.
4. Wait for the green **Connected** badge.

The Tools work now. For Genius, continue.

## 5. Add your API key (Genius only)

Genius needs your own key. Nothing is included with the app.

1. Get a key from one provider:
   [xAI](https://console.x.ai/), [OpenAI](https://platform.openai.com/api-keys),
   [Google AI Studio](https://aistudio.google.com/apikey) or
   [Anthropic](https://console.anthropic.com/).
2. In Live Actions open **Preferences → AI provider**, paste the key, and press **Test key**.
3. Pick a model from the list. Only models that work with tool calling are shown.

Your provider bills you for usage. The key is stored in
`%APPDATA%\Live Actions\settings.json` as plain text, on this PC only.

## 6. Optional: Live's browser for Genius

Without this step Genius can do everything except look inside Live's browser (packs, presets,
plug-ins).

In Live: **Settings → Link, Tempo & MIDI**, choose **LiveActionsRS** in any free Control Surface
slot, then restart Live once.

## Updating

Pull the new files (or unzip over the folder) and run `install.ps1` again. Then remove the Live
Actions device from its track and drag it back on: Max only reloads the device's script when it
is re-added.

## Uninstalling

Delete, in this order:

- the **Live Actions** folders under your User Library (`Presets\Audio Effects\Max Audio Effect\Live Actions`
  and `Remote Scripts\LiveActionsRS`)
- the Desktop shortcut
- `%APPDATA%\Live Actions` (your settings and saved keys)
- the registry key `HKEY_CURRENT_USER\Software\Classes\liveactions`
- this folder

## Troubleshooting

| Problem | Fix |
|---|---|
| "running scripts is disabled on this system" | Use the full command above, with `-ExecutionPolicy Bypass`. |
| The device is not in Live's browser | Restart Live, or right-click the User Library and rescan. Check the installer printed the right User Library path. |
| Badge stays red | The device must be on a track in the open Set. Ports 11924 and 11925 must be free on this PC. |
| "Live Actions can't start yet" | The message names what is missing: a Python package (run the installer again) or the WebView2 Runtime. |
| Genius: "No API key" | Preferences → AI provider. |
| Genius: no models listed | Press **Refresh models**. The key may be invalid, out of credit, or for a provider with no tool-calling models on your account. |
| Genius cannot browse or load presets | Do step 6. |
| A change to the device did nothing | Remove it from the track and drag it back on. |
