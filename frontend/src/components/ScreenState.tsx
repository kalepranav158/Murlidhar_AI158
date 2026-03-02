type ScreenStateProps = {
  loading: boolean;
  error: string | null;
  emptyMessage?: string;
};

export default function ScreenState({ loading, error, emptyMessage }: ScreenStateProps) {
  if (loading) {
    return <p className="muted">Loading...</p>;
  }

  if (error) {
    return <p className="error">{error}</p>;
  }

  if (emptyMessage) {
    return <p className="muted">{emptyMessage}</p>;
  }

  return null;
}
