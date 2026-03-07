import { lazy, Suspense, useCallback, useEffect, useState } from "react";
import DashboardPage from "./pages/DashboardPage";
import PracticePage from "./pages/PracticePage";
import CurriculumPage from "./pages/CurriculumPage";
import PracticeHistoryPage from "./pages/PracticeHistoryPage";
import AskPage from "./pages/AskPage";
import LoginPage from "./pages/LoginPage";
import { loginAuth, loginGoogleAuth, logoutAuth, verifyAuth } from "./api";
import {
  clearStoredAuth,
  getStoredAuthSession,
  getStoredAuthToken,
  setStoredAuthSession,
  setStoredAuthToken,
  type StoredAuthSession,
} from "./utils/authStorage";
import { setPreferredUserId } from "./utils/userIdentity";

const ProgressPage = lazy(() => import("./pages/ProgressPage"));
const SkillRadarPage = lazy(() => import("./pages/SkillRadarPage"));
const DiagnosticsPage = lazy(() => import("./pages/DiagnosticsPage"));
const AnalyticsPage = lazy(() => import("./pages/AnalyticsPage"));
const DocumentationPage = lazy(() => import("./pages/DocumentationPage"));
const LongNotesPage = lazy(() => import("./pages/LongNotesPage"));

type ViewKey =
  | "dashboard"
  | "practice"
  | "long-notes"
  | "curriculum"
  | "analytics"
  | "progress"
  | "practice-history"
  | "skill-radar"
  | "ask"
  | "diagnostics"
  | "documentation";

const navItems: Array<{ key: ViewKey; label: string }> = [
  { key: "dashboard", label: "Dashboard" },
  { key: "practice", label: "Practice Studio" },
  { key: "long-notes", label: "Long Notes" },
  { key: "curriculum", label: "Curriculum" },
  { key: "analytics", label: "Analytics" },
  { key: "progress", label: "Progress" },
  { key: "practice-history", label: "Practice History" },
  { key: "skill-radar", label: "Skill Radar" },
  { key: "ask", label: "Ask Guru" },
  { key: "diagnostics", label: "Debug" },
  { key: "documentation", label: "Documentation" },
];

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID?.trim() ?? "";

export default function App() {
  const [activeView, setActiveView] = useState<ViewKey>("dashboard");
  const [authSession, setAuthSession] =
    useState<StoredAuthSession | null>(() => getStoredAuthSession());
  const [authLoading, setAuthLoading] = useState<boolean>(() => Boolean(getStoredAuthToken()));
  const [authSubmitting, setAuthSubmitting] = useState(false);
  const [authGoogleSubmitting, setAuthGoogleSubmitting] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  useEffect(() => {
    const token = getStoredAuthToken();
    if (!token) {
      setAuthLoading(false);
      return;
    }

    let cancelled = false;
    void verifyAuth()
      .then((payload) => {
        if (cancelled) {
          return;
        }

        if (!payload.authenticated) {
          throw new Error("Session is not valid. Please sign in again.");
        }

        const nextSession: StoredAuthSession = {
          username: payload.username,
          authProvider: payload.auth_provider ?? "password",
          email: payload.email ?? null,
          expiresAt: payload.expires_at ?? null,
        };

        setStoredAuthSession(nextSession);
        setPreferredUserId(nextSession.email ?? nextSession.username);
        setAuthSession(nextSession);
        setAuthError(null);
      })
      .catch((error) => {
        if (cancelled) {
          return;
        }

        clearStoredAuth();
        setAuthSession(null);
        setAuthError(error instanceof Error ? error.message : "Session expired. Please sign in.");
      })
      .finally(() => {
        if (!cancelled) {
          setAuthLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const onLogin = useCallback(async (username: string, password: string) => {
    setAuthSubmitting(true);
    setAuthError(null);

    try {
      const payload = await loginAuth({ username, password });
      setStoredAuthToken(payload.access_token);

      const nextSession: StoredAuthSession = {
        username: payload.username,
        authProvider: payload.auth_provider ?? "password",
        email: payload.email ?? null,
        expiresAt: payload.expires_at ?? null,
      };

      setStoredAuthSession(nextSession);
      setPreferredUserId(nextSession.email ?? nextSession.username);
      setAuthSession(nextSession);
      setActiveView("dashboard");
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : "Sign-in failed. Please try again.");
    } finally {
      setAuthSubmitting(false);
    }
  }, []);

  const onGoogleLogin = useCallback(async (credential: string) => {
    setAuthGoogleSubmitting(true);
    setAuthError(null);

    try {
      const payload = await loginGoogleAuth({ credential });
      setStoredAuthToken(payload.access_token);

      const nextSession: StoredAuthSession = {
        username: payload.username,
        authProvider: payload.auth_provider ?? "google",
        email: payload.email ?? null,
        expiresAt: payload.expires_at ?? null,
      };

      setStoredAuthSession(nextSession);
      setPreferredUserId(nextSession.email ?? nextSession.username);
      setAuthSession(nextSession);
      setActiveView("dashboard");
    } catch (error) {
      setAuthError(
        error instanceof Error
          ? error.message
          : "Google sign-in failed. Please try username/password.",
      );
    } finally {
      setAuthGoogleSubmitting(false);
    }
  }, []);

  const onLogout = useCallback(async () => {
    try {
      await logoutAuth();
    } catch {
      // Ignore network/logout failures and always clear local session.
    }

    clearStoredAuth();
    setAuthSession(null);
    setActiveView("dashboard");
  }, []);

  const authSubmittingAny = authSubmitting || authGoogleSubmitting;

  const renderLazyPage = (element: JSX.Element) => {
    return (
      <Suspense
        fallback={
          <div className="container">
            <section className="card">
              <p className="muted">Loading page...</p>
            </section>
          </div>
        }
      >
        {element}
      </Suspense>
    );
  };

  if (authLoading) {
    return (
      <div className="container auth-shell">
        <section className="card auth-card">
          <p className="muted">Checking authentication...</p>
        </section>
      </div>
    );
  }

  if (!authSession) {
    return (
      <LoginPage
        loading={authSubmittingAny}
        error={authError}
        onSubmit={onLogin}
        onGoogleCredential={onGoogleLogin}
        googleClientId={GOOGLE_CLIENT_ID}
      />
    );
  }

  return (
    <>
      <header className="app-nav-wrap">
        <div className="app-nav-meta">
          <div className="app-nav-meta-text">
            <p className="app-nav-user">
              Signed in as <strong>{authSession.username}</strong>
              {authSession.authProvider === "google" ? " via Google" : ""}
            </p>
            {authSession.email && <p className="app-nav-email">{authSession.email}</p>}
          </div>
          <button className="tab-btn logout-btn" onClick={onLogout}>
            Logout
          </button>
        </div>
        <nav className="app-nav">
          {navItems.map((item) => (
            <button
              key={item.key}
              className={item.key === activeView ? "tab-btn active" : "tab-btn"}
              onClick={() => setActiveView(item.key)}
            >
              {item.label}
            </button>
          ))}
        </nav>
      </header>

      {activeView === "dashboard" && <DashboardPage />}
      {activeView === "practice" && <PracticePage />}
      {activeView === "long-notes" && renderLazyPage(<LongNotesPage />)}
      {activeView === "curriculum" && <CurriculumPage />}
      {activeView === "analytics" && renderLazyPage(<AnalyticsPage />)}
      {activeView === "progress" && renderLazyPage(<ProgressPage />)}
      {activeView === "practice-history" && <PracticeHistoryPage />}
      {activeView === "skill-radar" && renderLazyPage(<SkillRadarPage />)}
      {activeView === "ask" && <AskPage />}
      {activeView === "diagnostics" && renderLazyPage(<DiagnosticsPage />)}
      {activeView === "documentation" && renderLazyPage(<DocumentationPage />)}
    </>
  );
}
