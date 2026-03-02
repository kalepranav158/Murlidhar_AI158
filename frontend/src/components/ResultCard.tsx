import type { AsyncState } from "../types/ui";

type ResultCardProps = {
  title: string;
  state: AsyncState<unknown>;
};

export default function ResultCard({ title, state }: ResultCardProps) {
  return (
    <article className="result-card">
      <h3>{title}</h3>
      {state.loading && <p className="muted">Loading...</p>}
      {state.error && <p className="error">{state.error}</p>}
      {!state.loading && !state.error && state.data !== null && (
        <pre>{JSON.stringify(state.data, null, 2)}</pre>
      )}
      {!state.loading && !state.error && state.data === null && (
        <p className="muted">No response loaded yet.</p>
      )}
    </article>
  );
}
