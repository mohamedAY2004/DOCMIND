# DocMind Frontend — Explained From Absolute Zero

> You "vibe-coded" this frontend and want to actually understand it well enough to answer **any** question in your grad defense. This document starts from "what even is a frontend" and walks all the way up to the exact files in *your* project. Read it top to bottom once. Then re-read the **"Exam questions"** section at the end the night before.
>
> Every code snippet here is from **your real code**, with the file path shown.

---

## Table of contents

1. [The 30-second pitch (memorize this)](#1-the-30-second-pitch)
2. [How the web works (the absolute basics)](#2-how-the-web-works)
3. [Your tech stack — what each tool does and why](#3-your-tech-stack)
4. [React fundamentals (the part you said you don't know)](#4-react-fundamentals)
5. [How the app boots up (the startup chain)](#5-how-the-app-boots-up)
6. [Project folder structure](#6-project-folder-structure)
7. [Routing — how URLs map to screens](#7-routing)
8. [Authentication: tokens, sessions, login flow](#8-authentication-tokens-and-sessions)
9. [The API layer (services) and endpoints](#9-the-api-layer-and-endpoints)
10. [State management & custom hooks](#10-state-management-and-custom-hooks)
11. [The chat feature, end to end](#11-the-chat-feature-end-to-end)
12. [The styling system (Tailwind + theming)](#12-the-styling-system)
13. [Design patterns used in this codebase](#13-design-patterns)
14. [Full request lifecycle (one diagram to rule them all)](#14-full-request-lifecycle)
15. [Exam questions & model answers](#15-exam-questions--model-answers)
16. [Glossary](#16-glossary)

---

## 1. The 30-second pitch

> "The DocMind frontend is a **React single-page application** built with **Vite**. It talks to a **FastAPI backend** over HTTP using **Axios**. Users log in and get a **JWT token**, which we store in the browser and attach to every request. Based on the user's **role** (student, instructor, admin) we show different pages, enforced by **route guards**. The main feature is an **AI chat** over uploaded documents and subject materials, with optimistic UI updates and a typewriter streaming effect. Styling is **Tailwind CSS** with a custom theme that supports light/dark mode."

That paragraph alone answers ~40% of likely questions. The rest of this doc makes sure you can defend every word of it.

---

## 2. How the web works

Before React, understand the plumbing.

- **Frontend** = the code that runs *in the user's browser* (what they see and click).
- **Backend** = the code that runs *on a server* (database, business logic, AI). Yours is FastAPI (Python).
- They talk over **HTTP** — the same protocol as visiting a website. The frontend sends a **request** ("give me the subjects"), the backend sends a **response** (a list of subjects as **JSON**).

**JSON** is just text shaped like JavaScript objects, e.g.:
```json
{ "id": "u_1", "name": "Sara", "role": "student" }
```

**HTTP methods** (you'll be asked this):
| Method | Meaning | Example in your app |
|--------|---------|---------------------|
| `GET` | read data | get list of subjects |
| `POST` | create something | log in, send a chat message |
| `PATCH` | partially update | rename a conversation |
| `PUT` | replace | set a user's subjects |
| `DELETE` | remove | delete a conversation |

**HTTP status codes** (also commonly asked):
- `200` OK, `201` Created, `204` No Content (success, nothing to return)
- `400` Bad Request, `401` Unauthorized (not logged in / bad token), `403` Forbidden (logged in but not allowed), `404` Not Found
- `500` Server error

**SPA (Single-Page Application)** — your app is one HTML page (`index.html`). When you click "Chat", the browser does **not** reload a new page from the server. JavaScript swaps the visible content and changes the URL. This makes it feel like a desktop app. React + React Router make this possible.

---

## 3. Your tech stack

Everything below is from `frontend/package.json`. Here's what each dependency is for:

**Core:**
- **`react` + `react-dom`** — the UI library. `react` defines components; `react-dom` renders them into the browser's DOM (the live page).
- **`vite`** — the **build tool / dev server**. It serves your code instantly while developing (`npm run dev`) and bundles it for production (`npm run build`). Think "the thing that turns your many files into something a browser can run, fast."
- **`react-router-dom`** — **client-side routing**. Maps URLs (`/chat`, `/admin`) to components without a full page reload.

**Networking:**
- **`axios`** — HTTP client. The thing that actually sends requests to your backend. (You *could* use the browser's built-in `fetch`, but Axios is nicer: interceptors, timeouts, automatic JSON.)

**UI / UX:**
- **`tailwindcss`** — utility-CSS framework. You style by adding classes like `p-4 bg-dm-card` instead of writing separate CSS files.
- **`framer-motion`** — animations (fade-ins, slide-ins on the login form, message bubbles).
- **`lucide-react`** — icon set (the little SVG icons like the paperclip, trash can).
- **`sonner`** — toast notifications (the little pop-ups: "Conversation deleted").
- **`react-loading-skeleton`** — gray placeholder boxes while data loads.

**Chat rendering (the AI answers):**
- **`react-markdown`** — renders the AI's Markdown text as real formatting (bold, lists, tables).
- **`remark-gfm`** — adds GitHub-flavored Markdown (tables, strikethrough).
- **`remark-math` + `rehype-katex` + `katex`** — render LaTeX math equations (important for a university tool).
- **`rehype-highlight`** — syntax highlighting for code blocks.

**Data / reports:**
- **`recharts`** — charts on the admin analytics page.
- **`jspdf` + `jspdf-autotable`** — generate PDF reports (feedback reports).

> **If asked "why React and not plain JavaScript?"**: React lets you build the UI as reusable **components** and automatically re-renders the screen when **data changes**, instead of manually finding and updating DOM elements. It scales to a large app like this without becoming spaghetti.

---

## 4. React fundamentals

This is the section you specifically asked for. Read it slowly — everything else builds on it.

### 4.1 Components

A **component** is a JavaScript function that returns UI. That's it. Your whole app is a tree of components.

```jsx
function PrimaryButton({ children }) {
  return <button>{children}</button>
}
```

You then *use* it like an HTML tag: `<PrimaryButton>Login</PrimaryButton>`.

Real example — `frontend/src/components/ui/PrimaryButton.jsx`:
```1:23:frontend/src/components/ui/PrimaryButton.jsx
import { primaryButtonClass } from '../../constants/themeClasses'

function PrimaryButton({
  children,
  type = 'button',
  className = '',
  fullWidth = true,
  ...props
}) {
  return (
    <button
      type={type}
      className={[primaryButtonClass, fullWidth && 'w-full', className]
        .filter(Boolean)
        .join(' ')}
      {...props}
    >
      {children}
    </button>
  )
}

export default PrimaryButton
```

### 4.2 JSX

The HTML-looking stuff inside the function is **JSX**. It's not HTML — it's JavaScript that *looks* like HTML. Vite compiles it into real function calls. Key differences from HTML:
- `class` becomes `className` (because `class` is a reserved word in JS).
- You embed JavaScript with curly braces: `{user.name}`.
- Every tag must close: `<input />`.

### 4.3 Props

**Props** = the inputs you pass to a component (like function arguments). In `PrimaryButton` above, `children`, `type`, `className` are props. `children` is special: it's whatever you put *between* the tags.

```jsx
<PrimaryButton type="submit" className="mt-2">Login</PrimaryButton>
//             └── prop ──┘  └── prop ──┘    └─ children ─┘
```

Props flow **down** (parent → child) and are **read-only**. A child can't change its own props.

### 4.4 State (`useState`)

**State** = data that can change over time and, when it changes, causes the component to **re-render** (redraw itself). This is React's superpower.

From your login page (`frontend/src/pages/Login.jsx`):
```30:34:frontend/src/pages/Login.jsx
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState({})
  const [loading, setLoading] = useState(false)
```

`useState('')` gives you two things: the current value (`username`) and a setter (`setUsername`). When the user types, `onChange` calls `setUsername(...)`, React updates the value and re-renders so the input shows the new text.

> **Why not just a normal variable?** A normal variable change doesn't tell React to redraw. State does. This is *the* central idea: **UI = function(state)**. Change state → React recomputes the UI.

### 4.5 Hooks

**Hooks** are special functions starting with `use` that let a component "hook into" React features. Rules: only call them at the **top level** of a component (never inside loops/ifs).

The ones you use everywhere:
- **`useState`** — local state (above).
- **`useEffect`** — run code as a **side effect** (after render): fetching data, timers, subscriptions. Runs when its **dependency array** changes.
- **`useCallback`** — memoize (cache) a function so it isn't recreated every render. Important for performance and for stable dependencies.
- **`useMemo`** — memoize a computed value (e.g. a filtered/sorted list).
- **`useRef`** — a "box" that holds a value across renders **without** triggering re-renders (e.g. a reference to a DOM element, or a "is busy" flag).
- **`useContext`** — read shared data from a Context (see 4.7).

**`useEffect` example** — load student-access status when the login page mounts (`Login.jsx`):
```37:49:frontend/src/pages/Login.jsx
  useEffect(() => {
    let cancelled = false
    getStudentAccess().then((data) => {
      if (cancelled || data.enabled) return
      setStudentAccessNote(
        data.message?.trim() ||
          'Student access is currently paused. You can still sign in; student features will be unavailable until access is restored.',
      )
    })
    return () => {
      cancelled = true
    }
  }, [])
```
The `[]` at the end means "run once, when the component first appears." The returned function is a **cleanup** that runs when the component disappears. The `cancelled` flag prevents updating state after the component is gone (a common bug source).

### 4.6 The "custom hook" idea

A **custom hook** is just a function that uses other hooks, so you can reuse stateful logic across components. Your project has many: `useAuth`, `useChat`, `useConversations`, `useAsync`, `useTheme`, `useStreamingText`. They all live in `frontend/src/hooks/`. We'll cover the important ones in section 10.

### 4.7 Context (sharing data without "prop drilling")

Problem: the logged-in user is needed by many components at different depths. Passing `user` through every prop manually ("prop drilling") is painful.

Solution: **Context** — a way to provide a value at the top of the tree and read it anywhere below.

You use this for **auth** and **theme**. Pattern (from `frontend/src/hooks/useTheme.jsx`):
```5:38:frontend/src/hooks/useTheme.jsx
const ThemeContext = createContext({ theme: 'dark', toggleTheme: () => {} })

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored === 'light' || stored === 'dark') return stored
    } catch {}
    return 'dark'
  })

  useEffect(() => {
    const root = document.documentElement
    root.classList.remove('light', 'dark')
    root.classList.add(theme)
    try {
      localStorage.setItem(STORAGE_KEY, theme)
    } catch {}
  }, [theme])

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))
  }, [])

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export default function useTheme() {
  return useContext(ThemeContext)
}
```
Three parts to remember: **createContext** (make it), **Provider** (supply the value, wraps the app), **useContext** (read it anywhere). Any component can now call `useTheme()` to get `{ theme, toggleTheme }`.

---

## 5. How the app boots up

Here is the exact chain from "browser opens the page" to "app on screen." Be able to recite this.

**Step 1 — `frontend/index.html`** is the only HTML file. It has an empty `<div id="root"></div>` and loads your JS. It also has a tiny script that pre-applies the saved theme to avoid a flash:
```11:20:frontend/index.html
    <script>
      try {
        const t = localStorage.getItem('docmind-theme');
        if (t === 'light') document.documentElement.classList.replace('dark', 'light');
      } catch {}
    </script>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
```

**Step 2 — `frontend/src/main.jsx`** finds that `#root` div and tells React to render `<App />` into it:
```1:10:frontend/src/main.jsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```
`StrictMode` is a dev-only helper that double-invokes some logic to surface bugs. It does nothing in production.

**Step 3 — `frontend/src/App.jsx`** sets up the global "providers" (the wrappers that supply shared services to the whole tree):
```8:28:frontend/src/App.jsx
function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <AuthProvider>
          <StudentAccessNavigationBridge />
          <AppRoutes />
          <Toaster
            position="top-right"
            ...
          />
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  )
}
```
Read the nesting outside-in — this **order matters**:
1. `ThemeProvider` — light/dark theme available everywhere.
2. `BrowserRouter` — enables URL-based routing (must wrap anything that navigates).
3. `AuthProvider` — login state available everywhere (must be inside Router because it uses `useNavigate`).
4. `StudentAccessNavigationBridge` — a tiny helper (renders nothing) that lets non-React code redirect (explained in section 8).
5. `AppRoutes` — the actual screens.
6. `Toaster` — the global container that renders all toast pop-ups.

**Step 4 — `AppRoutes`** decides which page to show based on the URL. → section 7.

---

## 6. Project folder structure

```
frontend/
├─ index.html              # the single HTML page
├─ package.json            # dependencies + scripts (npm run dev/build/lint)
├─ vite.config.js          # Vite config (enables the React plugin)
├─ tailwind.config.js      # design tokens, colors, animations
├─ postcss.config.js       # plumbing for Tailwind
├─ eslint.config.js        # linting rules (code quality)
└─ src/
   ├─ main.jsx             # entry point (renders <App/>)
   ├─ App.jsx              # global providers + router
   ├─ index.css            # Tailwind directives + theme CSS variables
   ├─ assets/              # images (logos)
   ├─ constants/           # fixed values (branding, theme classes, enums)
   ├─ routes/              # route definitions + the ProtectedRoute guard
   ├─ pages/               # one component per screen/URL
   │  └─ admin/            # admin-only screens
   ├─ features/            # feature-specific UI (analytics charts)
   ├─ components/          # reusable UI
   │  ├─ ui/               # buttons, inputs, cards, message bubbles…
   │  ├─ layout/           # page shells (AppLayout, AdminLayout, top bar)
   │  ├─ chat/             # chat-specific components
   │  └─ admin/            # admin modals/forms
   ├─ hooks/               # custom hooks (useAuth, useChat, useAsync…)
   ├─ services/            # API calls (axios). NO UI here.
   └─ utils/               # pure helper functions (formatters, grouping)
```

**The golden rule of this codebase** (from your project rules): **pages compose components; components are small and reusable; API calls live only in `services/`; styling is Tailwind-only (no inline `style={{}}`).** Knowing this layering is itself an exam answer about "architecture."

---

## 7. Routing

### 7.1 What routing is

Routing = "which component do I show for this URL?" Handled entirely in the browser by **React Router**. No server round-trip when navigating.

### 7.2 Your route map

All defined in `frontend/src/routes/index.jsx`:
```36:71:frontend/src/routes/index.jsx
export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<RootRedirect />} />
      <Route path="/login" element={<LoginGate />} />

      {/* Student routes */}
      <Route element={<ProtectedRoute allowedRoles={['student']} />}>
        <Route element={<StudentAccessGate />}>
          <Route path="/home" element={<UserHome />} />
          <Route path="/chat" element={<ChatWithDoc />} />
          <Route path="/tutors" element={<ChatWithTutors />} />
          <Route path="/tutors/chat" element={<TutorChat />} />
          <Route path="/student-unavailable" element={<StudentUnavailable />} />
        </Route>
      </Route>

      {/* Instructor routes */}
      <Route element={<ProtectedRoute allowedRoles={['instructor']} />}>
        <Route path="/instructor" element={<InstructorHome />} />
        <Route path="/instructor/subject/:subjectId" element={<InstructorSubject />} />
      </Route>

      {/* Admin routes */}
      <Route element={<ProtectedRoute allowedRoles={['admin']} />}>
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/admin/users" element={<ManageUsers />} />
        ...
      </Route>
    </Routes>
  )
}
```

Things to notice (and explain in the defense):
- **`:subjectId`** is a **URL parameter** — `/instructor/subject/42` → the component reads `42`. (Read via `useParams()`.)
- Routes are **grouped by role**. The grouping wrapper `<Route element={<ProtectedRoute .../>}>` applies a guard to all routes nested inside it.
- Student routes have a **second** wrapper, `<StudentAccessGate />`, that can lock students out during exams/maintenance.

### 7.3 Redirect helpers

`RootRedirect` sends people who hit `/` to the right home based on login + role; `LoginGate` bounces already-logged-in users away from `/login`:
```22:34:frontend/src/routes/index.jsx
function RootRedirect() {
  const { isAuthenticated, role } = useAuth()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <Navigate to={HOME_BY_ROLE[role] || '/home'} replace />
}

function LoginGate() {
  const { isAuthenticated, role } = useAuth()
  if (isAuthenticated) {
    return <Navigate to={HOME_BY_ROLE[role] || '/home'} replace />
  }
  return <Login />
}
```
`<Navigate replace />` changes the URL. `replace` means "don't add a back-button entry" (so the user can't press Back into the login page after logging in).

### 7.4 The route guard (`ProtectedRoute`)

This is how you stop a student from opening `/admin`. File `frontend/src/routes/ProtectedRoute.jsx`:
```4:25:frontend/src/routes/ProtectedRoute.jsx
const HOME_BY_ROLE = {
  admin: '/admin',
  instructor: '/instructor',
  student: '/home',
}

function ProtectedRoute({ allowedRoles }) {
  const { isAuthenticated, role } = useAuth()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (allowedRoles && !allowedRoles.includes(role)) {
    return <Navigate to={HOME_BY_ROLE[role] || '/home'} replace />
  }

  return <Outlet />
}
```
Logic: not logged in → go to login. Logged in but wrong role → bounce to your own home. Otherwise render the nested routes via **`<Outlet />`** (Outlet = "render whatever child route matched here").

> **IMPORTANT for your defense — say this proactively:** This guard is **UX, not security**. A determined user can edit JavaScript in their browser. **Real security is enforced by the backend** (it checks the JWT and role on every request). The frontend guard just avoids showing screens the user can't use. Examiners love this point.

---

## 8. Authentication: tokens and sessions

This is the topic you flagged. Let's nail it.

### 8.1 What is a token? (JWT)

When you log in, the backend gives you a **JWT (JSON Web Token)** — a long signed string. Think of it as a **tamper-proof wristband** at a concert: it proves who you are and what you're allowed to do, and the server signed it so it can't be faked. Per your backend docs, the token's payload contains `sub` (user id), `role`, `jti` (a unique token id), and `exp` (expiry time).

Your frontend treats the token as **opaque** — it doesn't decode it; it just stores it and sends it back on every request.

### 8.2 What is a "session" here?

There's **no server-side session cookie**. Your "session" is simply: *the token + user info stored in the browser's `localStorage`*. As long as a valid token sits in `localStorage`, the user is "logged in." Logging out = deleting it.

**`localStorage`** = a small key-value store in the browser that **persists across tabs and page reloads** (unlike memory, which is wiped on refresh). That's why you stay logged in after refreshing.

Your two keys (from `frontend/src/hooks/useAuth.jsx`):
```9:10:frontend/src/hooks/useAuth.jsx
const AUTH_TOKEN_KEY = 'auth_token'
const AUTH_USER_KEY = 'auth_user'
```

### 8.3 The Auth context — single source of truth for "who is logged in"

`frontend/src/hooks/useAuth.jsx` wraps the whole app (`AuthProvider`) and exposes `user`, `token`, `role`, `isAuthenticated`, `login`, `logout`.

On startup it **reads existing auth from `localStorage`** so a refresh keeps you logged in:
```21:38:frontend/src/hooks/useAuth.jsx
function readStoredAuth() {
  try {
    const token = localStorage.getItem(AUTH_TOKEN_KEY)
    const raw = localStorage.getItem(AUTH_USER_KEY)
    if (token && raw) {
      const user = JSON.parse(raw)
      return { token, user, role: user.role }
    }
  } catch {
    /* corrupted — treat as logged-out */
  }
  return { token: null, user: null, role: null }
}
...
  const [auth, setAuth] = useState(readStoredAuth)
```

After a successful login it **persists** token + user and updates state (which re-renders the app, flipping `isAuthenticated` to true):
```41:58:frontend/src/hooks/useAuth.jsx
  const completeLogin = useCallback(({ token, user, redirect, welcomeMessage }) => {
    clearAllAuthStorage()
    localStorage.setItem(AUTH_TOKEN_KEY, token)
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user))
    setAuth({ token, user, role: user.role })
    toast.success(welcomeMessage ?? `Welcome back, ${user.name || user.username}!`, {
      description: `Signed in as ${user.role}`,
    })
    return redirect
  }, [])

  const login = useCallback(
    async (username, password) => {
      const result = await authLogin(username, password)
      return completeLogin(result)
    },
    [completeLogin],
  )
```

`isAuthenticated` is derived — just "is there a token?":
```68:78:frontend/src/hooks/useAuth.jsx
  const value = useMemo(
    () => ({
      user: auth.user,
      token: auth.token,
      role: auth.role,
      isAuthenticated: !!auth.token,
      login,
      logout,
    }),
    [auth, login, logout],
  )
```
(`useMemo` here prevents handing a brand-new object to consumers on every render, which would cause needless re-renders.)

### 8.4 How the token gets attached to every request (Axios request interceptor)

You don't manually add the token in each API call. The Axios instance does it automatically. File `frontend/src/services/apiClient.js`:
```13:25:frontend/src/services/apiClient.js
const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: DEFAULT_TIMEOUT,
  headers: { 'Content-Type': 'application/json' },
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```
A **request interceptor** is a function that runs **before every request leaves**. Here it grabs the token and sets the `Authorization: Bearer <token>` header — the standard way to send a JWT. The backend reads this header to identify you.

### 8.5 How expired/invalid sessions are handled (Axios response interceptor)

A **response interceptor** runs on **every response coming back**. Yours handles two special error cases globally so individual screens don't have to:
```27:48:frontend/src/services/apiClient.js
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    if (status === 403 && error.response?.data?.code === STUDENT_ACCESS_DISABLED) {
      goToStudentUnavailable()
      return Promise.reject(error)
    }
    if (status === 401) {
      // Do not hard-redirect on failed login — that reloads the page and hides
      // inline error messages. Other 401s mean an expired/invalid session.
      const url = String(error.config?.url ?? '')
      const isLoginAttempt = /\/auth\/login\/?$/.test(url) || url.endsWith('auth/login')
      if (!isLoginAttempt) {
        localStorage.removeItem('auth_token')
        localStorage.removeItem('auth_user')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)
```
Translation:
- **`401 Unauthorized`** on any normal request = your token expired or is invalid → wipe storage and kick to `/login`. (Exception: a failed **login** also returns 401 but we *don't* redirect — we want to show "wrong password" inline.)
- **`403` with code `STUDENT_ACCESS_DISABLED`** = admins turned off student access (e.g. during exams) → send to the "unavailable" page.

### 8.6 The login flow, start to finish

1. User types username/password in `Login.jsx`, hits submit.
2. `handleSubmit` validates fields, then calls `login()` from the auth context:
```65:72:frontend/src/pages/Login.jsx
    try {
      const redirect = await login(username.trim(), password)
      navigate(redirect, { replace: true })
    } catch (err) {
      setError(err.message || 'Invalid username or password.')
      setLoading(false)
    }
```
3. `login()` → `authService.login()` → `POST /auth/login` (`frontend/src/services/authService.js`):
```19:40:frontend/src/services/authService.js
export async function login(username, password) {
  try {
    const { data } = await apiClient.post('/auth/login', { username, password })
    return data
  } catch (err) {
    const status = err?.response?.status
    const code = err?.response?.data?.code

    if (status === 403 && code === STUDENT_ACCESS_DISABLED) {
      const wrapped = new Error(
        extractServerMessage(
          err,
          'Student access is currently disabled. Please try again later.',
        ),
      )
      wrapped.code = STUDENT_ACCESS_DISABLED
      throw wrapped
    }

    throw new Error(extractServerMessage(err, 'Invalid username or password.'))
  }
}
```
4. Backend returns `{ token, user, redirect }`. `completeLogin` stores them and returns the `redirect` URL.
5. The page calls `navigate(redirect)` → React Router shows the right home screen. Done.

### 8.7 Logout

```60:66:frontend/src/hooks/useAuth.jsx
  const logout = useCallback(() => {
    authLogout()
    clearAllAuthStorage()
    setAuth({ token: null, user: null, role: null })
    navigate('/login', { replace: true })
    toast('Signed out successfully')
  }, [navigate])
```
`authLogout()` calls `POST /auth/logout` (so the backend can **revoke** the token's `jti` — meaning even if someone copied the token, it's now blacklisted server-side), then we clear storage and reset state. Note it clears storage even if the network call fails — "best effort" logout.

### 8.8 The "navigation bridge" trick (why it exists)

Problem: `apiClient.js` is a plain module, **not** a React component, so it can't use React Router's `useNavigate()` hook to redirect on `403 STUDENT_ACCESS_DISABLED`. Solution: a tiny invisible component registers the navigate function into a shared variable that the plain module can call.

`frontend/src/utils/studentAccessNavigation.js`:
```1:15:frontend/src/utils/studentAccessNavigation.js
/** Registered from inside <Router> so apiClient can navigate without importing React. */
let navigateRef = null

export function registerStudentAccessNavigation(navigate) {
  navigateRef = navigate
}

export function goToStudentUnavailable() {
  if (navigateRef) {
    navigateRef('/student-unavailable', { replace: true })
  } else {
    window.location.assign('/student-unavailable')
  }
}
```
And the bridge component (`frontend/src/components/StudentAccessNavigationBridge.jsx`) registers it on mount. This is the **"service locator"** pattern — a clever workaround you can point to as a thoughtful design decision.

---

## 9. The API layer and endpoints

### 9.1 Why a separate `services/` folder

**All** network calls live in `frontend/src/services/`. UI components never call Axios directly. Benefits: one place to change an endpoint, consistent error handling, components stay focused on rendering. This is the **Service Layer / separation-of-concerns** pattern.

### 9.2 The shared client

Everything imports the one configured Axios instance from `apiClient.js`. The base URL comes from an environment variable, with a fallback:
```5:5:frontend/src/services/apiClient.js
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'
```
`import.meta.env.VITE_API_BASE_URL` is set in `frontend/.env` (e.g. `http://localhost:8000`). **Env vars must be prefixed `VITE_`** for Vite to expose them to the browser.

There are also **timeout presets** because AI generation and big uploads take much longer than a normal request:
```54:55:frontend/src/services/apiClient.js
export const UPLOAD_TIMEOUT = { timeout: 5 * 60_000 } // 5 minutes — large PDFs
export const LLM_TIMEOUT = { timeout: 6 * 60_000 }    // 6 minutes — LLM generation + reranking can be slow
```

### 9.3 The service files and what they cover

| File | Responsibility |
|------|----------------|
| `authService.js` | login / logout |
| `subjectService.js` | subjects, semesters, materials, instructor test-bot |
| `chatService.js` | doc chat + tutor chat conversations, messages, files, feedback |
| `uploadService.js` | multipart material uploads |
| `adminService.js` | users, subjects CRUD, semesters, stats, feedback, analytics |
| `systemAccessService.js` | the global student-access on/off flag |

A service function is tiny and predictable — call endpoint, return `data`:
```17:27:frontend/src/services/subjectService.js
export async function getStudentSubjects() {
  const { data } = await apiClient.get('/subjects/student')
  return data
}

export async function getInstructorSubjects(instructorId) {
  const { data } = await apiClient.get('/subjects/instructor', {
    params: instructorId ? { instructorId } : undefined,
  })
  return data
}
```
`params` become the **query string** (`/subjects/instructor?instructorId=...`).

### 9.4 Endpoint cheat-sheet (memorize the shapes, not every URL)

These are documented right in your service files. Examples:

**Auth** — `POST /auth/login`, `POST /auth/logout`
**Subjects** — `GET /subjects/student`, `GET /subjects/instructor`, `GET /subjects/:id`, `GET /subjects/:id/materials`, `POST /subjects/:id/materials` (upload), `GET /semesters`
**Doc chat** — `GET/POST /chat/doc/conversations`, `GET /chat/doc/conversations/:id/messages`, `POST /chat/doc/conversations/:id/messages`, file sub-routes
**Tutor chat** — `GET/POST /chat/tutor/conversations`, `.../:id/messages`
**Feedback** — `POST /chat/messages/:id/feedback`
**Admin** — `/admin/users`, `/admin/subjects`, `/admin/semesters`, `/admin/feedback`, `/admin/analytics/daily`
**System** — `GET /system/student-access`, `PATCH /admin/system/student-access`

> If asked an endpoint you don't remember: "All endpoints are centralized in `src/services/`, each file documents its backend contract in a header comment." That's a perfectly good answer.

### 9.5 File uploads (multipart)

Normal requests send JSON. File uploads send **`multipart/form-data`** via `FormData`. From `uploadService.js`:
```11:26:frontend/src/services/uploadService.js
export async function uploadMaterial(subjectId, file, { name, onUploadProgress } = {}) {
  const formData = new FormData()
  formData.append('file', file)
  if (name) formData.append('name', name)

  const { data } = await apiClient.post(
    `/subjects/${subjectId}/materials`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      ...UPLOAD_TIMEOUT,
      ...(onUploadProgress ? { onUploadProgress } : {}),
    },
  )
  return data
}
```
`onUploadProgress` lets you show a progress bar. The longer `UPLOAD_TIMEOUT` is spread in so big PDFs don't time out.

---

## 10. State management and custom hooks

You do **not** use Redux or any external state library. State management is: **`useState` locally + Context for global (auth/theme) + custom hooks to package reusable logic**. That's a legitimate, modern, lightweight choice — say so.

### 10.1 `useAsync` — the generic "load data" hook

Most "fetch on screen open" logic is the same: set loading, fetch, store data or error, handle unmount. `frontend/src/hooks/useAsync.js` packages it:
```12:43:frontend/src/hooks/useAsync.js
export default function useAsync(fn, deps = []) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const cancelledRef = useRef(false)

  const run = useCallback(async () => {
    cancelledRef.current = false
    setLoading(true)
    setError(null)
    try {
      const result = await fn()
      if (cancelledRef.current) return
      setData(result)
    } catch (err) {
      if (cancelledRef.current) return
      setError(err)
    } finally {
      if (!cancelledRef.current) setLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  useEffect(() => {
    run()
    return () => {
      cancelledRef.current = true
    }
  }, [run])

  return { data, error, loading, refresh: run, setData }
}
```
A page just does `const { data, loading, error } = useAsync(getStudentSubjects, [])` and renders accordingly. `cancelledRef` (a `useRef`) prevents the "set state after unmount" warning.

### 10.2 `useConversations` — the chat list controller

Used by both doc-chat and tutor-chat. It's a great example of **reuse via parameters**: you pass it the `fetcher`/`remover`/`updater` functions and it handles the list, the active selection, toasts, and **optimistic updates**:
```77:114:frontend/src/hooks/useConversations.js
  const deleteConversation = useCallback(
    async (id) => {
      if (!remover) return
      const snapshot = conversations
      setConversations((prev) => prev.filter((c) => c.id !== id))
      if (activeId === id) setActiveId(null)
      try {
        await remover(id)
        toast.success('Conversation deleted.')
      } catch {
        setConversations(snapshot)
        toast.error('Could not delete the conversation.')
      }
    },
    [conversations, activeId, remover],
  )
```
**Optimistic update** (a key term to know): we remove the item from the UI **immediately** (snappy feel), then call the server. If the server fails, we **roll back** to the saved `snapshot`. Same pattern is used for rename.

### 10.3 `useChat` / `useTutorChat` — message controllers

These own the message list for an open conversation. They:
1. Load stored history when the conversation id changes (`useEffect`).
2. On send, **optimistically** add the user's message with a temporary id.
3. Call the API, then swap the temp id for the real server id.
4. Stream the AI reply in (next section).
5. On error, show a friendly message and **remove** the optimistic message.

Optimistic send from `useChat.js`:
```125:167:frontend/src/hooks/useChat.js
      busyRef.current = true
      setErrorMessage('')
      setLastFailedText('')
      const tempId = `user-${Date.now()}`
      setMessages((prev) => [
        ...prev,
        { id: tempId, role: 'user', text: trimmed },
      ])
      setStatus('loading')
      setIsTyping(true)

      try {
        const { userMessage, reply } = await sendDocMessage(
          conversationId,
          trimmed,
        )

        setMessages((prev) =>
          prev.map((m) =>
            m.id === tempId && userMessage?.id
              ? { ...m, id: userMessage.id }
              : m,
          ),
        )

        const msgId = reply?.id || `doc-${Date.now()}`
        const replyText = reply?.text || ''
        setMessages((prev) => [
          ...prev,
          { id: msgId, role: 'doc', text: '' },
        ])
        setIsTyping(false)
        streamReply(replyText, msgId)
      } catch (err) {
        const msg = friendlyError(err)
        setStatus('error')
        setErrorMessage(msg)
        setLastFailedText(trimmed)
        busyRef.current = false
        setIsTyping(false)
        // Remove the optimistic user message so the UI stays clean
        setMessages((prev) => prev.filter((m) => m.id !== tempId))
      }
```
The `busyRef` guard prevents sending two messages at once. `friendlyError` maps backend error codes (timeout, `FILES_NOT_READY`, `VALIDATION_ERROR`, 500) to human messages — good error UX.

### 10.4 `useStreamingText` — the typewriter effect

Important honesty point for your defense: **the streaming is a frontend animation, not true token-by-token server streaming.** The backend returns the full reply at once; this hook reveals it a few characters at a time with a timer to *feel* like ChatGPT.
```5:34:frontend/src/hooks/useStreamingText.js
export default function useStreamingText(setMessages, onComplete) {
  const [streamingId, setStreamingId] = useState(null)
  const intervalRef = useRef(null)

  const streamReply = useCallback((fullText, msgId) => {
    let charIndex = 0
    setStreamingId(msgId)

    intervalRef.current = setInterval(() => {
      const nextChunk = Math.min(charIndex + 2 + Math.floor(Math.random() * 3), fullText.length)
      charIndex = nextChunk

      setMessages((prev) =>
        prev.map((m) => (m.id === msgId ? { ...m, text: fullText.slice(0, nextChunk) } : m)),
      )

      if (charIndex >= fullText.length) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
        setStreamingId(null)
        onComplete?.()
      }
    }, STREAM_INTERVAL_MS)
  }, [setMessages, onComplete])

  const stopStreaming = useCallback(() => {
    if (intervalRef.current) clearInterval(intervalRef.current)
    intervalRef.current = null
    setStreamingId(null)
  }, [])

  return { streamingId, streamReply, stopStreaming }
}
```
`setInterval` reveals 2–4 more characters every 30ms; when done it clears the timer. `stopStreaming` is called when you switch conversations so a stale timer doesn't keep typing. (If an examiner asks "is this real streaming?", be honest: "No — it's a cosmetic reveal of an already-complete response. Real streaming would use Server-Sent Events or chunked responses; this was a UX choice.")

### 10.5 `useStudentAccessGate` — polling for the global flag

Loads the student-access policy and **re-checks** it every 60s and whenever the window regains focus, so a student gets locked out mid-session if admins flip the switch:
```33:50:frontend/src/hooks/useStudentAccessGate.jsx
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh()
  }, [refresh])

  useEffect(() => {
    const id = window.setInterval(refresh, POLL_MS)
    return () => window.clearInterval(id)
  }, [refresh])

  useEffect(() => {
    const onFocus = () => {
      refresh()
    }
    window.addEventListener('focus', onFocus)
    return () => window.removeEventListener('focus', onFocus)
  }, [refresh])
```
The `StudentAccessGate` component (a layout route) uses this to redirect to `/student-unavailable` when disabled.

---

## 11. The chat feature, end to end

Two chat modes share most code:
- **Doc chat** (`/chat`): a student uploads their own PDFs and chats about them.
- **Tutor chat** (`/tutors/chat`): a student chats with a subject's AI tutor built from instructor-uploaded materials.

### 11.1 The component hierarchy

```
ChatWithDoc (page)         ← owns conversation list + files, talks to services
  └─ ChatScreen            ← the whole chat UI; owns useChat(activeId)
       ├─ ChatHeader
       ├─ ChatSidebar      ← list of past conversations
       └─ main
            ├─ file chips (the attached PDFs)
            ├─ messages    ← maps messages → ChatMessageBubble
            ├─ TypingIndicator
            ├─ ErrorBanner
            └─ input form  ← textbox + paperclip + send
```

The page (`ChatWithDoc.jsx`) wires the list hook to the doc-chat services and passes everything down as props:
```44:49:frontend/src/pages/ChatWithDoc.jsx
  } = useConversations({
    fetcher: listDocConversations,
    remover: deleteDocConversation,
    updater: updateDocConversation,
  })
```

### 11.2 The "upload then chat" flow (doc chat)

1. No conversation yet → `ChatScreen` shows `FileUploadPrompt`.
2. User drops a PDF → `handleFirstUpload` → `createDocConversation([file])` (`POST /chat/doc/conversations` as multipart). A new conversation is created and **prepended** to the sidebar.
3. The PDF is **processing** (being parsed + embedded on the backend). The page **polls** `listDocFiles` every 3s until status flips off `processing`:
```82:107:frontend/src/pages/ChatWithDoc.jsx
  useEffect(() => {
    if (!activeId) return
    if (!files.some((f) => f.status === 'processing')) return
    let cancelled = false
    let timer = null
    const tick = async () => {
      try {
        const latest = await listDocFiles(activeId)
        if (cancelled) return
        const list = Array.isArray(latest) ? latest : latest?.items || []
        setFiles(list)
        if (list.every((f) => f.status !== 'processing')) {
          setUploadingFirstFileName('')
          return
        }
      } catch {
        /* transient */
      }
      if (!cancelled) timer = setTimeout(tick, PROCESSING_POLL_MS)
    }
    timer = setTimeout(tick, PROCESSING_POLL_MS)
    return () => {
      cancelled = true
      if (timer) clearTimeout(timer)
    }
  }, [activeId, files])
```
4. Once ready, the user types a question → `useChat.sendMessage` → optimistic user bubble → `POST .../messages` → reply streams in.

### 11.3 How AI answers are rendered

The `ChatMessageBubble` renders assistant text through `react-markdown` with math + code + table plugins, so the AI's Markdown becomes real formatting:
```122:131:frontend/src/components/ui/ChatMessageBubble.jsx
          {isAssistant ? (
            <div className="chat-prose prose prose-sm max-w-none">
              <Markdown
                remarkPlugins={remarkPlugins}
                rehypePlugins={rehypePlugins}
              >
                {text}
              </Markdown>
              {streaming && <StreamingCursor />}
            </div>
```
User messages are rendered as plain text (`whitespace-pre-wrap`) — you never run Markdown on user input (also safer). Each assistant message has **copy** and **thumbs up/down feedback** buttons that call the feedback endpoints.

### 11.4 Auto-scroll

`useAutoScroll(messagesRef, [messages, isTyping])` scrolls the message list to the bottom whenever messages change — a 5-line hook using `useEffect` + `scrollTo`.

---

## 12. The styling system

### 12.1 Tailwind in one minute

Instead of writing CSS files, you compose **utility classes** directly in JSX: `className="p-4 bg-dm-card rounded-xl"` means padding, card background, rounded corners. Your project rule is **Tailwind only — no inline `style={{}}`, no CSS modules.**

### 12.2 Design tokens & theming (this is the clever part)

Colors aren't hardcoded. They're **CSS variables** defined per theme in `frontend/src/index.css`:
```15:34:frontend/src/index.css
@layer base {
  :root,
  .dark {
    --dm-background:       15 28 29;
    --dm-card:             20 43 44;
    --dm-primary:          13 110 115;
    ...
    color-scheme: dark;
  }

  .light {
    --dm-background:       244 247 247;
    --dm-card:             255 255 255;
    ...
  }
```
Tailwind then maps friendly names (`bg-dm-card`, `text-dm-primary`) to those variables in `tailwind.config.js`:
```14:27:frontend/tailwind.config.js
      colors: {
        dm: {
          background:      'rgb(var(--dm-background) / <alpha-value>)',
          card:            'rgb(var(--dm-card) / <alpha-value>)',
          primary:         'rgb(var(--dm-primary) / <alpha-value>)',
          ...
        },
      },
```
**How dark/light mode works:** `useTheme` adds the class `light` or `dark` to the `<html>` element. That single class swap changes which set of CSS variables is active, so every `dm-*` color flips at once. The values are stored as raw RGB channels (`15 28 29`) so Tailwind's opacity modifiers like `bg-dm-card/80` work.

### 12.3 Shared class strings & animations

Repeated style combos live in `frontend/src/constants/themeClasses.js` (e.g. `primaryButtonClass`) so buttons stay consistent. Custom keyframe animations (`float`, `message-in`, `typing-dot`, etc.) are defined in `tailwind.config.js`.

---

## 13. Design patterns

Name-drop these confidently; each has a concrete file behind it.

| Pattern | Where | One-line explanation |
|---------|-------|----------------------|
| **Component-based architecture** | all of `components/`, `pages/` | UI built from small reusable pieces |
| **Container/Presentational** | `ChatWithDoc` (logic) vs `ChatScreen`/`ChatMessageBubble` (display) | pages fetch data; components just render props |
| **Provider / Context** | `AuthProvider`, `ThemeProvider` | share global state without prop drilling |
| **Custom hooks (composition)** | `hooks/` | reuse stateful logic across components |
| **Service layer** | `services/` | all API access isolated from UI |
| **Interceptor / middleware** | `apiClient.js` | cross-cutting auth + error handling on every request/response |
| **Higher-order route / guard** | `ProtectedRoute`, `StudentAccessGate` | wrap routes to enforce access rules |
| **Optimistic UI with rollback** | `useConversations`, `useChat` | update UI first, revert on failure |
| **Polling** | `ChatWithDoc` file status, `useStudentAccessGate` | repeatedly re-fetch to track async server state |
| **Service locator / bridge** | `studentAccessNavigation.js` + bridge component | let non-React code trigger navigation |
| **Factory of clients / config singleton** | single `apiClient` instance | one configured object reused everywhere |
| **Render props / slots** | `AppLayout` (`sidebar`, `topNav`, `children`) | pass UI sections as props for flexible layouts |

---

## 14. Full request lifecycle

Tie it all together — the journey of "student sends a tutor chat message":

```
[User types question, hits Enter]
        │
        ▼
useTutorChat.sendMessage()                    (hooks/useTutorChat.js)
  • optimistically add user bubble (temp id)
  • ensureConversation(): if new, POST /chat/tutor/conversations
        │
        ▼
sendTutorMessage(id, text)                     (services/chatService.js)
        │
        ▼
apiClient.post(...)                            (services/apiClient.js)
  • request interceptor adds  Authorization: Bearer <JWT>
  • LLM_TIMEOUT (6 min) applied
        │
        ▼  HTTP over network
FastAPI backend
  • verifies JWT + role + subject access
  • runs RAG: embed question → vector search → LLM answer
  • returns { userMessage, reply }
        │
        ▼  response comes back
apiClient response interceptor                 (handles 401/403 globally)
        │
        ▼
useTutorChat:
  • swap temp user id → real id
  • add empty assistant bubble
  • useStreamingText reveals reply char-by-char
        │
        ▼
ChatMessageBubble renders Markdown/math        (components/ui/ChatMessageBubble.jsx)
useAutoScroll keeps view pinned to bottom
```

---

## 15. Exam questions & model answers

Practice saying these out loud.

**Q: What is React and why use it?**
A: A JavaScript library for building UIs from reusable components. The UI is a function of state — when state changes, React efficiently re-renders. We chose it for component reuse, a large ecosystem, and maintainability on a multi-role app like this.

**Q: What's the difference between props and state?**
A: Props are read-only inputs passed from a parent. State is internal, mutable data owned by a component; changing it (via the setter) triggers a re-render.

**Q: What is a hook? Name some you use.**
A: A function letting components use React features. Built-in: `useState`, `useEffect`, `useCallback`, `useMemo`, `useRef`, `useContext`. Custom: `useAuth`, `useChat`, `useConversations`, `useAsync`, `useStreamingText`, `useTheme`.

**Q: How does authentication work?**
A: Login posts credentials to `/auth/login`; the backend returns a JWT plus user info. We store both in `localStorage`. An Axios request interceptor attaches `Authorization: Bearer <token>` to every call. On a `401`, a response interceptor clears storage and redirects to login. Logout calls `/auth/logout` so the backend revokes the token's `jti`, then we clear local storage.

**Q: Where is the session stored and why localStorage vs cookies?**
A: In `localStorage` (`auth_token`, `auth_user`). It persists across reloads and tabs and is simple to attach as a Bearer header. Trade-off: it's readable by JS so it's vulnerable to XSS; httpOnly cookies are safer against XSS but need CSRF protection and server cookie handling. For this project we went with the Bearer-token approach. (Good, honest nuance to show awareness.)

**Q: How do you protect routes by role?**
A: `ProtectedRoute` reads auth from context; if not logged in it redirects to `/login`, if the role isn't allowed it redirects to that role's home, otherwise it renders nested routes via `<Outlet/>`. Students get an extra `StudentAccessGate`. Crucially, this is UX only — **real authorization is enforced on the backend per request.**

**Q: How does the frontend talk to the backend?**
A: Through a single configured Axios instance (`apiClient`) with a base URL from `VITE_API_BASE_URL`. All calls are wrapped in `services/` functions. Interceptors handle auth and global errors; timeout presets handle slow uploads and LLM calls.

**Q: Is the chat really streaming?**
A: No — the backend returns the full answer; `useStreamingText` reveals it character-by-character with a timer for a ChatGPT-like feel. True streaming would need SSE/chunked responses.

**Q: What is optimistic UI?**
A: Updating the UI immediately as if the request succeeded (e.g. showing the sent message or removing a deleted conversation), then reverting if the server returns an error. It makes the app feel instant. We do this in `useConversations` and the chat hooks.

**Q: How does dark/light mode work?**
A: `ThemeProvider` toggles a `light`/`dark` class on `<html>` and saves the choice in `localStorage`. CSS variables defined per class hold the colors; Tailwind maps `dm-*` utilities to those variables, so one class swap re-themes everything.

**Q: How is the project structured / what architecture?**
A: Layered and feature-organized: `pages` (screens) compose `components` (reusable UI); `services` isolate API calls; `hooks` hold reusable logic; `routes` define navigation and guards; `constants`/`utils` hold shared values and pure helpers. Styling is Tailwind-only.

**Q: What is Vite?**
A: The build tool and dev server. Fast hot-reload in development, optimized bundle for production. Replaces older tooling like Create React App/Webpack.

**Q: How do uploads work?**
A: Via `FormData` with `multipart/form-data` content type and an extended timeout. After upload, the file is processed (parsed + embedded) on the backend; we poll its status until it's ready.

**Q: How do you handle errors?**
A: Three layers — global interceptors (401/403), per-service try/catch that throws clean messages, and per-hook `friendlyError` helpers mapping backend error codes to user-friendly text shown via toasts or an `ErrorBanner`, often with a Retry action.

**Q: What happens on page refresh — why am I still logged in?**
A: On startup `AuthProvider` reads the token/user back from `localStorage` (`readStoredAuth`), so state is rehydrated and the app stays authenticated until the token expires or the user logs out.

---

## 16. Glossary

- **SPA** — Single-Page Application; one HTML page, JS swaps content.
- **Component** — a function returning UI.
- **JSX** — HTML-like syntax inside JavaScript.
- **Props** — inputs to a component (read-only).
- **State** — mutable component data that triggers re-render on change.
- **Hook** — a `use*` function adding React capabilities.
- **Context / Provider** — share data across the tree without prop drilling.
- **Render / re-render** — React (re)computing what the UI should look like.
- **DOM** — the live tree of elements the browser displays.
- **Route / router** — URL-to-component mapping handled in the browser.
- **Guard** — a wrapper that blocks/redirects based on rules.
- **JWT** — signed token proving identity + role.
- **localStorage** — persistent key-value store in the browser.
- **Interceptor** — function running on every request/response.
- **Service layer** — modules that own all API calls.
- **Optimistic update** — update UI before the server confirms, roll back on error.
- **Polling** — periodically re-fetching to track server-side changes.
- **Multipart / FormData** — how files are uploaded over HTTP.
- **Toast** — small transient notification pop-up.
- **Tailwind** — utility-class CSS framework.
- **Design token** — a named style value (color) reused via CSS variables.
- **Vite** — the build tool / dev server.
- **Axios** — the HTTP client library.

---

### Final advice for the defense
1. Lead with the **30-second pitch** (section 1).
2. If you blank, fall back to the **layering**: "URL → route guard → page → hook → service → Axios (with interceptors) → backend → back up the chain → component renders."
3. Be **honest** about the two "illusion" parts (frontend route guards are UX not security; chat streaming is cosmetic). Examiners respect that far more than bluffing.

You've got this. Read it twice and you'll understand your own project better than most people who hand-wrote one.
