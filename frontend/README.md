# DocMind Frontend

![Node](https://img.shields.io/badge/Node.js-v20%2B-339933?logo=nodedotjs&logoColor=white)
![License](https://img.shields.io/badge/License-Unlicensed-blue)

**DocMind** is an AI-powered document assistant that lets students chat with uploaded documents, interact with subject-specific tutors, and gives instructors tools to manage course materials and monitor student engagement. A dedicated admin panel provides user management, subject oversight, and usage analytics — all through a clean, modern web interface.

## Features

- **Chat with Documents** — Upload a PDF, PPTX, or PNG and have an AI-powered conversation about its contents.
- **Chat with Tutors** — Browse subjects and chat with AI tutors trained on course materials.
- **Instructor Dashboard** — Manage subjects, upload and track course materials, test the student-facing bot, and view usage analytics.
- **Admin Panel** — Full admin dashboard with user management, subject statistics, feedback review, and usage analytics with interactive charts.
- **Role-Based Access** — Separate experiences for students, instructors, and admins with JWT authentication and protected routes.
- **Responsive UI** — Dark-themed interface with custom Tailwind design tokens, the Poppins typeface, and Framer Motion animations.

The public marketing site lives in the sibling [`docmind-landing`](../docmind-landing) repository. It is standalone and does not link into this application.

---

## Tech Stack

| Technology | Purpose |
|---|---|
| [React 19](https://react.dev/) | UI library |
| [Vite 7](https://vite.dev/) | Build tool and dev server (SWC plugin) |
| [Tailwind CSS 3](https://tailwindcss.com/) | Utility-first CSS framework |
| [React Router 7](https://reactrouter.com/) | Client-side routing with protected routes |
| [Axios](https://axios-http.com/) | HTTP client for API requests |
| [Framer Motion](https://motion.dev/) | Declarative animations and transitions |
| [Recharts](https://recharts.org/) | Composable charting library for analytics |
| [Sonner](https://sonner.emilkowal.dev/) | Toast notifications |
| [Lucide React](https://lucide.dev/) | Icon library |

---

## Requirements

| Tool | Recommended Version |
|---|---|
| **Node.js** | v20 or later (developed on v24.13) |
| **npm** | v10 or later (developed on v11.8) |

> **Tip:** Use [nvm](https://github.com/nvm-sh/nvm) (macOS/Linux) or [nvm-windows](https://github.com/coreybutler/nvm-windows) to manage Node versions.

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yeagx/docmind-frontend.git
```

### 2. Navigate into the project

```bash
cd docmind-frontend
```

### 3. Install dependencies

```bash
npm install
```

### 4. Start the development server

```bash
npm run dev
```

The app will be available at **http://localhost:5173** by default.

---

## Available Scripts

| Command | Description |
|---|---|
| `npm run dev` | Start the Vite development server with hot module replacement. |
| `npm run build` | Create an optimized production build in the `dist/` folder. |
| `npm run preview` | Serve the production build locally for testing. |
| `npm run lint` | Run ESLint across the project to catch code quality issues. |

---

## Environment Variables

Create a `.env` file in the project root to configure the backend API URL:

```bash
VITE_API_BASE_URL=http://localhost:8000/api
```

Vite exposes variables prefixed with `VITE_` to client code via `import.meta.env`. The API client in `src/services/apiClient.js` reads `VITE_API_BASE_URL` and falls back to `/api` if unset. See the [Vite env documentation](https://vite.dev/guide/env-and-mode) for details.

> **Note:** Never commit `.env` files containing secrets. The root `.gitignore` already excludes `.env` and `.env.*`.

---

## Project Structure

```
src/
├── App.jsx                  # Root component — BrowserRouter, AuthProvider, Toaster
├── main.jsx                 # Application entry point
├── index.css                # Global styles, Tailwind directives, and design tokens
│
├── components/
│   ├── chat/                # Chat-related components
│   │   ├── ChatScreen.jsx          # Document chat interface
│   │   ├── ChatSidebar.jsx         # Chat history sidebar
│   │   ├── TutorChatScreen.jsx     # Subject tutor chat interface
│   │   ├── TypingIndicator.jsx     # Animated typing dots
│   │   └── TestStudentBotModal.jsx # Instructor bot preview modal
│   │
│   ├── layout/              # App shell and navigation
│   │   ├── AppLayout.jsx    # Main layout wrapper (fixed / scrollable)
│   │   ├── AppTopBar.jsx    # Top navigation bar
│   │   ├── AppSidebar.jsx   # Sidebar navigation
│   │   ├── AdminLayout.jsx  # Admin panel layout (sidebar nav, logout)
│   │   └── index.js         # Layout barrel export
│   │
│   └── ui/                  # Reusable UI primitives
│       ├── ActionCard.jsx
│       ├── AuthCard.jsx
│       ├── AuthHeader.jsx
│       ├── ChatMessageBubble.jsx
│       ├── FileUploadPrompt.jsx
│       ├── GradientBackdrop.jsx    # Reusable gradient background
│       ├── InputField.jsx
│       ├── InstructorSubjectCard.jsx
│       ├── PageFooter.jsx
│       ├── PasswordField.jsx
│       ├── PrimaryButton.jsx
│       ├── ProcessingState.jsx
│       ├── StatBox.jsx
│       ├── SubjectCard.jsx
│       └── UploadZone.jsx
│
├── data/                    # Centralized data constants
│   ├── subjects.js          # Subject definitions and lookup helpers
│   └── adminMockData.js     # Mock users, subject stats, feedback, and activity
│
├── hooks/                   # Custom React hooks
│   ├── useAuth.jsx          # Auth context provider and consumer hook
│   ├── useAutoScroll.js     # Auto-scroll hook for chat views
│   ├── useChat.js           # Document chat state management
│   └── useTutorChat.js      # Tutor chat state management
│
├── pages/                   # Route-level page components
│   ├── Login.jsx
│   ├── UserHome.jsx
│   ├── ChatWithDoc.jsx
│   ├── ChatWithTutors.jsx
│   ├── TutorChat.jsx
│   ├── InstructorHome.jsx
│   ├── InstructorSubject.jsx
│   └── admin/
│       ├── AdminDashboard.jsx   # Metrics, quick nav, system status, activity
│       ├── ManageUsers.jsx      # User table with search, filter, and pagination
│       ├── ManageSubjects.jsx   # Subject stats and feedback panel
│       └── Analytics.jsx        # Interactive charts (line, bar, pie)
│
├── routes/
│   ├── index.jsx            # Centralized route definitions
│   └── ProtectedRoute.jsx   # Role-based route guard
│
├── services/                # API and business logic layer
│   ├── index.js             # Barrel export for all services
│   ├── apiClient.js         # Axios instance with auth interceptors
│   ├── authService.js       # Login / logout
│   ├── chatService.js       # Document and tutor chat messaging
│   ├── mockChat.js          # Mock AI responses (dev only)
│   ├── subjectService.js    # Subject CRUD operations
│   └── uploadService.js     # File upload handling
│
├── utils/                   # Shared utility functions
│   └── formatters.js        # formatFileSize, formatTime, etc.
│
└── assets/
    └── docmind-logo.png     # Application logo
```

---

## Architecture Overview

### Routing

All routes are defined in `src/routes/index.jsx`. The app uses React Router v7 with `BrowserRouter`. A `ProtectedRoute` wrapper checks authentication status and role before rendering child routes.

| Path | Component | Role | Description |
|---|---|---|---|
| `/` | RootRedirect | — | Redirects to `/login` or the user's role-based home |
| `/login` | LoginGate | public | Login form (redirects authenticated users) |
| `/home` | UserHome | student | Student hub |
| `/chat` | ChatWithDoc | student | Upload a document and chat about it |
| `/tutors` | ChatWithTutors | student | Subject picker |
| `/tutors/chat` | TutorChat | student | Subject-specific tutor chat (`?subject=`) |
| `/instructor` | InstructorHome | instructor | Instructor subject list |
| `/instructor/subject/:subjectId` | InstructorSubject | instructor | Subject detail (materials, analytics, test bot) |
| `/admin` | AdminDashboard | admin | Admin dashboard overview |
| `/admin/users` | ManageUsers | admin | User management |
| `/admin/subjects` | ManageSubjects | admin | Subject stats and feedback |
| `/admin/analytics` | Analytics | admin | Usage analytics with interactive charts |

### Authentication

Authentication is managed via a React context (`AuthProvider` in `useAuth.jsx`) that wraps the entire app. It stores the JWT token and user object in `localStorage` and exposes `login()`, `logout()`, `isAuthenticated`, and `role` to all components.

| Credential | Role | Redirect |
|---|---|---|
| `user` / `user123` | student | `/home` |
| `instructor` / `instructor123` | instructor | `/instructor` |
| `1` / `123` | admin | `/admin` |

The `apiClient.js` interceptor attaches the Bearer token to every request and redirects to `/login` on 401 responses.

### Data Flow

Pages consume data through **services** (`src/services/`), which currently return mock data but are designed as drop-in replacements for real API calls. Each service file contains commented-out Axios calls ready to be uncommented when the backend is available. Admin pages consume mock data from `src/data/adminMockData.js`.

### Service Layer

The service layer is organized by domain:

| Service | Responsibility |
|---|---|
| `apiClient.js` | Centralized Axios instance with `VITE_API_BASE_URL`, auth token injection, and 401 auto-redirect |
| `authService.js` | `login()` and `logout()` — currently uses mock credentials |
| `chatService.js` | `sendDocMessage()` and `sendTutorMessage()` — wraps mock chat layer |
| `subjectService.js` | `getStudentSubjects()`, `getInstructorSubjects()`, `getSubjectById()` |
| `uploadService.js` | `uploadDocument()` and `uploadMaterial()` — mock file upload |

Import any service function from the barrel:

```js
import { login, sendDocMessage, uploadMaterial } from './services'
```

### Custom Hooks

| Hook | Purpose |
|---|---|
| `useAuth` | React context provider and consumer for authentication state (user, token, role, `login()`, `logout()`) |
| `useChat` | Manages document chat state (messages, sending, typing indicator, error handling) |
| `useTutorChat` | Manages tutor chat state (messages, input, suggestions, regeneration) |
| `useAutoScroll` | Scrolls a container to the bottom when dependencies change |

### Centralized Data

Subject definitions live in `src/data/subjects.js` and are the single source of truth used by student pages, instructor pages, and services. Use `getSubjectName(id)` to resolve a subject slug to its display name.

Admin mock data lives in `src/data/adminMockData.js` and provides mock users, subject statistics, feedback entries, and activity logs for the admin panel.

### Reusable Components

The `components/ui/` directory contains atomic UI primitives shared across pages:

- **GradientBackdrop** — Configurable gradient overlay with preset variants (`default`, `subtle`, `cards`, `corner`, `chat`, `vignette`)
- **PrimaryButton** — Standard call-to-action button
- **InputField / PasswordField** — Form inputs with icon and focus styling
- **ChatMessageBubble** — Message bubble with copy-to-clipboard, variants for doc chat, tutor chat, and modal
- **ActionCard / SubjectCard / InstructorSubjectCard** — Card patterns for different contexts
- **FileUploadPrompt / UploadZone** — Drag-and-drop file upload areas
- **ProcessingState** — Animated circular progress indicator
- **StatBox** — Metric display box for dashboards
- **PageFooter** — Consistent footer across pages

The `components/layout/` directory provides layout shells:

- **AppLayout** — Main layout with top bar, sidebar, and content area (student/instructor)
- **AdminLayout** — Admin panel layout with sidebar navigation and logout

---

## Backend Integration Guide

When the backend API is ready:

1. Set `VITE_API_BASE_URL` in your `.env` file.
2. In each service file, uncomment the real API call and remove or comment out the mock implementation.
3. Replace mock data in `src/data/adminMockData.js` with real API calls in new admin service files.
4. The `apiClient.js` interceptor automatically attaches the auth token from `localStorage` and redirects to `/login` on 401 responses.
5. Refer to `API_SPECIFICATION.md` for the full endpoint contract.

---

## Development Notes

- **Tailwind Design Tokens** — The project defines a custom `dm` color palette and card border-radius in `tailwind.config.js`. Use classes like `bg-dm-background`, `text-dm-muted`, and `rounded-card` to stay consistent.
- **Authentication** — The app uses JWT-based auth via a React context (`AuthProvider`). The login page calls `useAuth().login()` and redirects students to `/home`, instructors to `/instructor`, and admins to `/admin` based on role.
- **Route Guards** — `ProtectedRoute` in `src/routes/ProtectedRoute.jsx` wraps role-specific route groups and redirects unauthenticated or unauthorized users.
- **Routing** — All routes are defined in `src/routes/index.jsx`. The app uses React Router v7 with `BrowserRouter`.
- **Animations** — Framer Motion is used for page transitions and component animations.
- **Toasts** — Sonner provides toast notifications (success on login, info on logout, errors on failures).
- **Charts** — Recharts powers the interactive analytics charts in the admin panel.
- **Lint** — The project passes ESLint with zero errors and zero warnings. Run `npm run lint` before committing.

---

## Troubleshooting

### `npm install` fails

- Delete `node_modules/` and `package-lock.json`, then run `npm install` again.
- Make sure you are using Node.js v20 or later (`node -v` to check).

### Node version mismatch

```bash
nvm install 20
nvm use 20
```

Or on Windows with nvm-windows:

```bash
nvm install 20.x
nvm use 20.x
```

### Port 5173 already in use

Another process is using the default Vite port. Either stop that process or start Vite on a different port:

```bash
npm run dev -- --port 3000
```

### Blank page after `npm run dev`

- Open the browser console for errors.
- Ensure all dependencies are installed (`npm install`).
- Clear the browser cache or try an incognito window.

---

## Author

**Abdulrhman Mohamed** — [github.com/yeagx](https://github.com/yeagx)

---

## License

This project is currently unlicensed. Contact the author for usage terms.
