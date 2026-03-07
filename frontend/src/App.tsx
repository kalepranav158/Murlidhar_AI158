import { lazy, Suspense, useState } from "react";
import DashboardPage from "./pages/DashboardPage";
import PracticePage from "./pages/PracticePage";
import CurriculumPage from "./pages/CurriculumPage";
import PracticeHistoryPage from "./pages/PracticeHistoryPage";
import AskPage from "./pages/AskPage";

const ProgressPage = lazy(() => import("./pages/ProgressPage"));
const SkillRadarPage = lazy(() => import("./pages/SkillRadarPage"));
const DiagnosticsPage = lazy(() => import("./pages/DiagnosticsPage"));
const AnalyticsPage = lazy(() => import("./pages/AnalyticsPage"));
const DocumentationPage = lazy(() => import("./pages/DocumentationPage"));

type ViewKey =
  | "dashboard"
  | "practice"
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
  { key: "curriculum", label: "Curriculum" },
  { key: "analytics", label: "Analytics" },
  { key: "progress", label: "Progress" },
  { key: "practice-history", label: "Practice History" },
  { key: "skill-radar", label: "Skill Radar" },
  { key: "ask", label: "Ask Guru" },
  { key: "diagnostics", label: "Debug" },
  { key: "documentation", label: "Documentation" },
];

export default function App() {
  const [activeView, setActiveView] = useState<ViewKey>("dashboard");

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

  return (
    <>
      <header className="app-nav-wrap">
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
