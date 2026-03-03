import { useState } from "react";
import DashboardPage from "./pages/DashboardPage";
import PracticePage from "./pages/PracticePage";
import CurriculumPage from "./pages/CurriculumPage";
import ProgressPage from "./pages/ProgressPage";
import DiagnosticsPage from "./pages/DiagnosticsPage";

type ViewKey = "dashboard" | "practice" | "curriculum" | "progress" | "diagnostics";

const navItems: Array<{ key: ViewKey; label: string }> = [
  { key: "dashboard", label: "Dashboard" },
  { key: "practice", label: "Practice" },
  { key: "curriculum", label: "Curriculum" },
  { key: "progress", label: "Progress" },
  { key: "diagnostics", label: "Diagnostics" },
];

export default function App() {
  const [activeView, setActiveView] = useState<ViewKey>("dashboard");

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
      {activeView === "progress" && <ProgressPage />}
      {activeView === "diagnostics" && <DiagnosticsPage />}
    </>
  );
}
