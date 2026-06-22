# Anthology Track Data — Editor & JSON Workflow

Three files now work together:

- **anthology-v9.html** — the web prototype. Loads track data from `tracks.json` at runtime via `fetch()`.
- **tracks.json** — the data file. A JSON array of track objects.
- **anthology_editor.py** — a desktop GUI (Tkinter) for editing `tracks.json` without hand-writing JSON.

## Running the editor

Requires Python 3.8+ with Tkinter (bundled by default on Windows and macOS
installers from python.org; on Linux you may need `sudo apt install python3-tk`
or your distro's equivalent).

```
python3 anthology_editor.py
```

Keep `anthology_editor.py` and `tracks.json` in the **same folder**. The editor
opens `tracks.json` from its own directory automatically on launch. Use
**Load JSON…** if you want to point it at a different file, and **Save** /
**Save As…** to write changes back out.

### Editing a track

1. Select a track in the left-hand list (or click **+ New** to add one).
2. Edit the fields on the right:
   - **Volume** — I, II, or III (Ballads / Social Music / Songs)
   - **Order in volume** — its position within that volume's list (1, 2, 3…)
   - **Title, Artist, Year, Genre**
   - **Headline synopsis** — the Smith-style newspaper-headline summary
   - **Spotify track ID** — just the ID from the track's Spotify URL
     (`open.spotify.com/track/`**`THIS_PART`**), not the full URL. Leave blank
     if there's no linked recording yet.
   - **Image URL** / **Image credit** — leave both blank if there's no image yet.
3. Click **Apply changes to this track** to commit the form into memory.
4. Click **Save** (or **Save As…**) to write `tracks.json` to disk.

The display number shown in the list (e.g. `I·6`) is generated automatically
from the Volume + Order fields — you don't edit it directly.

Use **↑ / ↓** to reorder tracks within a volume, **Duplicate** to clone an
entry as a starting point, and **Delete** to remove one.

## Viewing the updated site

Because the HTML uses `fetch('tracks.json')`, the two files need to be served
from the same origin — opening the HTML directly as a `file://` URL will
**fail in some browsers** due to local-file fetch restrictions. If that
happens you'll see a small red banner at the bottom of the page saying it
fell back to built-in sample data.

To avoid this, serve the folder locally. From the folder containing both
files:

```
python3 -m http.server 8000
```

Then open `http://localhost:8000/anthology-v9.html` in your browser. Reload
the page after saving changes in the editor to see them reflected.

## tracks.json shape (for reference / hand-editing)

```json
[
  {
    "n": "I·1",
    "v": "I",
    "o": 1,
    "t": "Henry Lee",
    "a": "Dick Justice",
    "y": "1929",
    "g": "murder ballad",
    "h": "MAN SLAIN BY WOMAN HE REFUSES; BODY THROWN DOWN A WELL",
    "spotify": "3MoKGJEDhkWC0lVHOgSCiE",
    "img": null,
    "imgC": null
  }
]
```

`spotify`, `img`, and `imgC` should be `null` (not an empty string) when
there's no value — the HTML checks for `null`/falsy to decide whether to show
the "no recording linked" message or the image placeholder glyph.
