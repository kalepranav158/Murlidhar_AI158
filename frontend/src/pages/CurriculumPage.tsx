import { useMemo, useState } from "react";
import type { ChangeEvent } from "react";
import ScreenState from "../components/ScreenState";
import { useStudentProfile } from "../hooks/useStudentProfile";

export default function CurriculumPage() {
  const [userId, setUserId] = useState("demo_user");
  const { curriculumState, loadCurriculum } = useStudentProfile();

  const safeUserId = useMemo(() => userId.trim(), [userId]);

  const onUserIdChange = (event: ChangeEvent<HTMLInputElement>) => {
    setUserId(event.target.value);
  };

  const onLoadCurriculum = async () => {
    try {
      await loadCurriculum(safeUserId);
    } catch {
      return;
    }
  };

  const curriculum = curriculumState.data?.data;

  return (
    <div className="container">
      <h1>Curriculum</h1>

      <section className="card">
        <label>
          User ID
          <input value={userId} onChange={onUserIdChange} />
        </label>
        <div className="row">
          <button onClick={onLoadCurriculum}>Load Curriculum</button>
        </div>
      </section>

      <section className="card">
        <ScreenState
          loading={curriculumState.loading}
          error={curriculumState.error}
          emptyMessage={curriculumState.data?.empty.isEmpty ? curriculumState.data.empty.message ?? undefined : undefined}
        />

        {curriculum && !curriculumState.loading && !curriculumState.error && (
          <>
            <div className="grid">
              <article className="result-card">
                <h3>Level & Goal</h3>
                <p><strong>Current Level:</strong> {curriculum.currentLevel}</p>
                <p><strong>Composite Score:</strong> {curriculum.compositeScore ?? "N/A"}</p>
                <p><strong>Recommended:</strong> {curriculum.recommendedContent ?? "N/A"}</p>
                <p><strong>Next Goal:</strong> {curriculum.nextGoal ?? "N/A"}</p>
              </article>
              <article className="result-card">
                <h3>Why Recommended</h3>
                <p>{curriculum.reason ?? "No reason provided."}</p>
              </article>
            </div>

            <div className="grid">
              <article className="result-card">
                <h3>Unlocked Content</h3>
                {curriculum.unlockedContent.length === 0 ? (
                  <p className="muted">No unlocked content.</p>
                ) : (
                  <ul className="plain-list">
                    {curriculum.unlockedContent.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                )}
              </article>

              <article className="result-card">
                <h3>Mastered Content</h3>
                {curriculum.masteredContent.length === 0 ? (
                  <p className="muted">No mastered content yet.</p>
                ) : (
                  <ul className="plain-list">
                    {curriculum.masteredContent.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                )}
              </article>

              <article className="result-card">
                <h3>Locked Content</h3>
                {curriculum.lockedContent.length === 0 ? (
                  <p className="muted">No locked content.</p>
                ) : (
                  <ul className="plain-list">
                    {curriculum.lockedContent.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                )}
              </article>
            </div>
          </>
        )}
      </section>
    </div>
  );
}
