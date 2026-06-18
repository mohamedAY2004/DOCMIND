# Portal Demo

A **standalone, static presentation demo** that simulates how DocMind would be integrated into the AASTMT Student Portal as a first-party service.

> ⚠️ **Not part of the real project.** This folder is for presentation/demo purposes only.

---

## Flow

```
login.html  ──▶  portal.html  ──▶  sso-bridge.html  ──▶  DocMind App
  (Login)       (Dashboard)         (SSO handoff)        (localhost:5173)
```

### Pages

| File | Description |
|---|---|
| `login.html` | AASTMT portal login clone (Registration Number + Pin Code) |
| `portal.html` | Portal dashboard with all standard services + the DocMind card |
| `sso-bridge.html` | Animated SSO hand-off page that "passes" the session to DocMind |

---

## How to Use

1. **Open `login.html`** in any browser (no server needed — pure HTML/JS).
2. Enter **any** Registration Number and Pin Code (e.g. `2210097510` / `1234`).
3. Check the fake CAPTCHA checkbox and click **Login**.
4. You land on the **portal dashboard** — all standard services are decorative links.
5. Click the highlighted **DocMind – AI Study Assistant** card.
6. The **SSO bridge** animates the session hand-off, then redirects to the DocMind app.

---

## Configuration

By default the SSO bridge redirects to `http://localhost:5173` (Vite dev server).

To change the DocMind URL at runtime, set it in `sessionStorage` from the portal page:
```js
sessionStorage.setItem('docmind_url', 'http://your-server/');
```

Or simply edit the fallback in `sso-bridge.html`:
```js
const docmindUrl = sessionStorage.getItem('docmind_url') || 'http://localhost:5173';
```

---

## Images

Drop your images into the `images/` folder. See `images/README.md` for the full list.
All images are optional — pages show emoji fallbacks when files are missing.
