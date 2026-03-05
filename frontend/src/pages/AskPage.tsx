import { useMemo, useState } from "react";
import type { ChangeEvent } from "react";
import { askGuru } from "../api";
import ResultCard from "../components/ResultCard";
import { initialAsyncState } from "../types/ui";

export default function AskPage() {
  const [userId, setUserId] = useState("demo_user");
  const [question, setQuestion] = useState("How should I improve rhythm stability?");
  const [askState, setAskState] = useState(initialAsyncState<unknown>());

  const safeUserId = useMemo(() => userId.trim(), [userId]);

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

      <section className="grid">
        <ResultCard title="Ask" state={askState} />
      </section>
    </div>
  );
}