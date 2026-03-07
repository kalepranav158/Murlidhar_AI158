import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";

type LoginPageProps = {
  loading: boolean;
  error: string | null;
  onSubmit: (username: string, password: string) => Promise<void>;
  onGoogleCredential?: (credential: string) => Promise<void>;
  googleClientId?: string;
};

export default function LoginPage(props: LoginPageProps) {
  const { loading, error, onSubmit, onGoogleCredential, googleClientId } = props;
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [googleInitError, setGoogleInitError] = useState<string | null>(null);
  const googleButtonRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const clientId = googleClientId?.trim() ?? "";
    if (!clientId || !onGoogleCredential) {
      return;
    }

    let disposed = false;
    const scriptSelector = "script[data-venora-google-gsi='1']";
    let scriptToClean: HTMLScriptElement | null = null;

    const initializeGoogleButton = () => {
      if (disposed || !googleButtonRef.current) {
        return;
      }

      const googleAccountsId = window.google?.accounts?.id;
      if (!googleAccountsId) {
        setGoogleInitError("Google Sign-In could not be initialized.");
        return;
      }

      setGoogleInitError(null);
      googleButtonRef.current.innerHTML = "";

      googleAccountsId.initialize({
        client_id: clientId,
        callback: (response: GoogleCredentialResponse) => {
          const credential = response.credential?.trim();
          if (!credential) {
            setGoogleInitError("Google sign-in did not return a credential.");
            return;
          }

          void onGoogleCredential(credential);
        },
      });

      googleAccountsId.renderButton(googleButtonRef.current, {
        type: "standard",
        theme: "outline",
        size: "large",
        shape: "pill",
        text: "signin_with",
        logo_alignment: "left",
      });
    };

    const onScriptLoad = () => initializeGoogleButton();
    const onScriptError = () => {
      if (!disposed) {
        setGoogleInitError("Failed to load Google Sign-In script.");
      }
    };

    if (window.google?.accounts?.id) {
      initializeGoogleButton();
      return;
    }

    const existingScript = document.querySelector<HTMLScriptElement>(scriptSelector);
    if (existingScript) {
      scriptToClean = existingScript;
    } else {
      scriptToClean = document.createElement("script");
      scriptToClean.src = "https://accounts.google.com/gsi/client";
      scriptToClean.async = true;
      scriptToClean.defer = true;
      scriptToClean.dataset.venoraGoogleGsi = "1";
      document.head.appendChild(scriptToClean);
    }

    scriptToClean.addEventListener("load", onScriptLoad);
    scriptToClean.addEventListener("error", onScriptError);

    return () => {
      disposed = true;
      scriptToClean?.removeEventListener("load", onScriptLoad);
      scriptToClean?.removeEventListener("error", onScriptError);
    };
  }, [googleClientId, onGoogleCredential]);

  const googleEnabled = Boolean((googleClientId?.trim() ?? "") && onGoogleCredential);

  const onFormSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const safeUsername = username.trim();
    if (!safeUsername || !password) {
      return;
    }

    await onSubmit(safeUsername, password);
  };

  return (
    <div className="container auth-shell">
      <section className="auth-hero card">
        <p className="auth-kicker">Project Access</p>
        <h1 className="auth-title">VENORA</h1>
        <p className="muted auth-subtitle">Sign in to open your practice dashboard.</p>
      </section>

      <section className="card auth-card">
        <h2>Authentication</h2>
        <form className="auth-form" onSubmit={onFormSubmit}>
          <label>
            Username
            <input
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              autoComplete="username"
              placeholder="Enter username"
            />
          </label>

          <label>
            Password
            <input
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              type="password"
              autoComplete="current-password"
              placeholder="Enter password"
            />
          </label>

          {error && <p className="error">{error}</p>}

          <div className="row">
            <button type="submit" disabled={loading || !username.trim() || !password}>
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </div>

          {googleEnabled && (
            <>
              <div className="auth-divider" role="separator" aria-label="Alternative sign-in methods">
                <span>or continue with</span>
              </div>
              <div className="google-auth-wrap">
                <div className="google-button-host" ref={googleButtonRef} />
              </div>
            </>
          )}

          {!googleEnabled && (
            <p className="muted google-auth-note">
              Google Sign-In is disabled. Set <code>VITE_GOOGLE_CLIENT_ID</code> in
              <code> frontend/.env</code> to enable it.
            </p>
          )}

          {googleInitError && <p className="error">{googleInitError}</p>}
        </form>
      </section>
    </div>
  );
}
