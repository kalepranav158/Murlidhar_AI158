import { useMemo, useState } from "react";
import type { ChangeEvent } from "react";
import { askGuru } from "../api";
import ScreenState from "../components/ScreenState";
import { initialAsyncState } from "../types/ui";

const isObjectPayload = (value: unknown): value is Record<string, unknown> => {
  return typeof value === "object" && value !== null;
};

const toLabel = (key: string): string => {
  return key
    .split("_")
    .filter((part) => part.length > 0)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
};

type AskField = {
  key: string;
  value: string;
};

export default function AskPage() {
  const [userId, setUserId] = useState("demo_user");
  const [question, setQuestion] = useState("How should I improve rhythm stability?");
  const [askState, setAskState] = useState(initialAsyncState<unknown>());

  const safeUserId = useMemo(() => userId.trim(), [userId]);
  const askPayload = askState.data;
  const askObject = useMemo(() => {
    if (!isObjectPayload(askPayload)) {
      return null;
    }

    return askPayload;
  }, [askPayload]);
  const askMode = useMemo(() => {
    if (!askObject || typeof askObject.mode !== "string") {
      return null;
    }

    return askObject.mode;
  }, [askObject]);
  const askDescription = useMemo(() => {
    if (!askObject || typeof askObject.description !== "string") {
      return null;
    }

    const text = askObject.description.trim();
    return text.length > 0 ? text : null;
  }, [askObject]);
  const askConfidence = useMemo(() => {
    if (!askObject || typeof askObject.confidence_score !== "number") {
      return null;
    }

    const normalized = Math.max(0, Math.min(1, askObject.confidence_score));
    return `${Math.round(normalized * 100)}%`;
  }, [askObject]);

  const askFields = useMemo<AskField[]>(() => {
    if (!askObject) {
      return [];
    }

    const excluded = new Set(["mode", "description", "confidence_score"]);

    return Object.entries(askObject)
      .flatMap(([key, value]) => {
        if (excluded.has(key) || value === null || value === undefined) {
          return [];
        }

        if (typeof value === "string") {
          const text = value.trim();
          if (!text) {
            return [];
          }

          return [{ key, value: text }];
        }

        if (typeof value === "number") {
          return [{ key, value: Number.isFinite(value) ? `${value}` : "-" }];
        }

        if (typeof value === "boolean") {
          return [{ key, value: value ? "Yes" : "No" }];
        }

        return [{ key, value: JSON.stringify(value) }];
      })
      .sort((left, right) => left.key.localeCompare(right.key));
  }, [askObject]);

  const onUserIdChange = (event: ChangeEvent<HTMLInputElement>) => {
    setUserId(event.target.value);
  };

  const onQuestionChange = (event: ChangeEvent<HTMLInputElement>) => {
    setQuestion(event.target.value);
  };

  const onAskGuru = async () => {
    setAskState({ loading: true, error: null, data: null });

    try {
      const payload = await askGuru(safeUserId, {
        question: question.trim(),
      });
      setAskState({ loading: false, error: null, data: payload });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      setAskState({ loading: false, error: message, data: null });
    }
  };

  return (
    <div className="container">
      <h1>Ask Guru</h1>

      <section className="card">
        <label>
          User ID
          <input value={userId} onChange={onUserIdChange} />
        </label>
        <label>
          Question
          <input value={question} onChange={onQuestionChange} />
        </label>
        <div className="row">
          <button onClick={onAskGuru}>Ask Guru</button>
        </div>
      </section>

      <section className="card ask-response-panel">
        <h2>Guru Response</h2>
        <ScreenState
          loading={askState.loading}
          error={askState.error}
          emptyMessage="Ask a question to view structured guidance."
        />

        {!askState.loading && !askState.error && askObject && (
          <article className="ask-response-card">
            <div className="ask-response-head">
              <span className="ask-mode-badge">{askMode ? toLabel(askMode) : "Response"}</span>
              {askConfidence && <span className="ask-confidence-badge">Confidence {askConfidence}</span>}
            </div>

            {askDescription && <p className="ask-response-description">{askDescription}</p>}

            {askFields.length > 0 ? (
              <div className="ask-response-grid">
                {askFields.map((field) => (
                  <section key={field.key} className="ask-response-item">
                    <h3>{toLabel(field.key)}</h3>
                    <p>{field.value}</p>
                  </section>
                ))}
              </div>
            ) : (
              <p className="muted">No additional response fields available.</p>
            )}
          </article>
        )}

        {!askState.loading && !askState.error && askState.data !== null && !askObject && (
          <pre>{JSON.stringify(askState.data, null, 2)}</pre>
        )}
      </section>
    </div>
  );
}