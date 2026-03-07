import { useEffect, useMemo, useRef, useState } from "react";
import type { ChangeEvent } from "react";
import { getAnalyticsTrend, getSessions } from "../api";
import { isMessagePayload } from "../api/adapters";
import ScreenState from "../components/ScreenState";
import { EChartBase, type BaseChartOption } from "../modules/charts";
import {
  buildAnalyticsAccuracyTrendOption,
  buildAnalyticsInstabilityOption,
  buildAnalyticsPitchErrorOption,
  buildAnalyticsTimingErrorOption,
  type AnalyticsPoint,
} from "../modules/analytics/options/buildAnalyticsOptions";
import type { AnalyticsTrendApi, MessagePayload, SessionsApi } from "../types/api";
import { initialAsyncState, type AsyncState } from "../types/ui";

type AnalyticsChartPayload = {
  trend: AnalyticsTrendApi | MessagePayload;
  sessions: SessionsApi | MessagePayload;
};

export default function AnalyticsPage() {
  const [userId, setUserId] = useState("demo_user");
  const [chartState, setChartState] = useState<AsyncState<AnalyticsChartPayload>>(initialAsyncState());
  const hasLoadedOnVisitRef = useRef(false);

  const safeUserId = useMemo(() => userId.trim(), [userId]);
  const chartPayload = chartState.data;

  const accuracyPoints = useMemo<AnalyticsPoint[]>(() => {
    if (!chartPayload || isMessagePayload(chartPayload.trend)) {
      return [];
    }

    const series = chartPayload.trend.accuracy_series ?? [];
    return series.map((entry, index) => ({
      label: `S${entry.session ?? index + 1}`,
      value: typeof entry.accuracy === "number" ? Math.round(entry.accuracy * 10) / 10 : null,
    }));
  }, [chartPayload]);

  const sessionPoints = useMemo(() => {
    if (!chartPayload || isMessagePayload(chartPayload.sessions)) {
      return [] as Array<{ label: string; pitchError: number | null; timingError: number | null }>;
    }

    const sessions = [...(chartPayload.sessions.sessions ?? [])].reverse();
    return sessions.map((session, index) => {
      const label = `S${index + 1}`;
      const pitchError =
        typeof session.avg_pitch_error === "number"
          ? Math.round(Math.abs(session.avg_pitch_error) * 10) / 10
          : null;
      const timingError =
        typeof session.avg_timing_error === "number"
          ? Math.round(Math.abs(session.avg_timing_error) * 1000) / 1000
          : null;

      return {
        label,
        pitchError,
        timingError,
      };
    });
  }, [chartPayload]);

  const pitchErrorPoints = useMemo<AnalyticsPoint[]>(
    () => sessionPoints.map((item) => ({ label: item.label, value: item.pitchError })),
    [sessionPoints],
  );

  const timingErrorPoints = useMemo<AnalyticsPoint[]>(
    () => sessionPoints.map((item) => ({ label: item.label, value: item.timingError })),
    [sessionPoints],
  );

  const instabilityPoints = useMemo<AnalyticsPoint[]>(() => {
    const accuracyMap = new Map<string, number | null>(
      accuracyPoints.map((point) => [point.label, point.value]),
    );

    const clamp = (value: number): number => {
      if (value < 0) {
        return 0;
      }

      if (value > 100) {
        return 100;
      }

      return value;
    };

    return sessionPoints.map((item) => {
      const accuracy = accuracyMap.get(item.label);

      if (
        typeof accuracy !== "number" ||
        typeof item.pitchError !== "number" ||
        typeof item.timingError !== "number"
      ) {
        return {
          label: item.label,
          value: null,
        };
      }

      const accuracyRisk = clamp(100 - accuracy);
      const pitchRisk = clamp((item.pitchError / 50) * 100);
      const timingRisk = clamp((item.timingError / 0.5) * 100);
      const instability = (0.4 * accuracyRisk) + (0.35 * pitchRisk) + (0.25 * timingRisk);

      return {
        label: item.label,
        value: Math.round(instability * 10) / 10,
      };
    });
  }, [accuracyPoints, sessionPoints]);

  const accuracyTrendOption = useMemo<BaseChartOption | null>(() => {
    if (accuracyPoints.length === 0) {
      return null;
    }

    return buildAnalyticsAccuracyTrendOption(accuracyPoints);
  }, [accuracyPoints]);

  const pitchErrorOption = useMemo<BaseChartOption | null>(() => {
    if (pitchErrorPoints.length === 0) {
      return null;
    }

    return buildAnalyticsPitchErrorOption(pitchErrorPoints);
  }, [pitchErrorPoints]);

  const timingErrorOption = useMemo<BaseChartOption | null>(() => {
    if (timingErrorPoints.length === 0) {
      return null;
    }

    return buildAnalyticsTimingErrorOption(timingErrorPoints);
  }, [timingErrorPoints]);

  const instabilityOption = useMemo<BaseChartOption | null>(() => {
    if (instabilityPoints.length === 0) {
      return null;
    }

    return buildAnalyticsInstabilityOption(instabilityPoints);
  }, [instabilityPoints]);

  const chartEmptyMessage = useMemo(() => {
    if (!chartPayload) {
      return "Load analytics charts to inspect trend and stability signals.";
    }

    if (isMessagePayload(chartPayload.trend)) {
      return chartPayload.trend.message;
    }

    if (isMessagePayload(chartPayload.sessions)) {
      return chartPayload.sessions.message;
    }

    if (
      accuracyPoints.length === 0 &&
      pitchErrorPoints.length === 0 &&
      timingErrorPoints.length === 0 &&
      instabilityPoints.length === 0
    ) {
      return "No analytics chart data available.";
    }

    return undefined;
  }, [
    accuracyPoints.length,
    chartPayload,
    instabilityPoints.length,
    pitchErrorPoints.length,
    timingErrorPoints.length,
  ]);

  const runCall = async <T,>(setter: (next: AsyncState<T>) => void, fn: () => Promise<T>) => {
    setter({ loading: true, error: null, data: null });
    try {
      const payload = await fn();
      setter({ loading: false, error: null, data: payload });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      setter({ loading: false, error: message, data: null });
    }
  };

  const onLoadChartSet = async () => {
    await runCall(setChartState, async () => {
      const [trend, sessions] = await Promise.all([
        getAnalyticsTrend(safeUserId),
        getSessions(safeUserId, 60),
      ]);

      return {
        trend,
        sessions,
      };
    });
  };

  useEffect(() => {
    if (!safeUserId || hasLoadedOnVisitRef.current) {
      return;
    }

    hasLoadedOnVisitRef.current = true;
    void onLoadChartSet().catch(() => undefined);
  }, [safeUserId]);

  const onUserIdChange = (event: ChangeEvent<HTMLInputElement>) => {
    setUserId(event.target.value);
  };

  return (
    <div className="container">
      <h1>Analytics</h1>

      <section className="card">
        <label>
          User ID
          <input value={userId} onChange={onUserIdChange} />
        </label>
        <div className="row">
          <button onClick={onLoadChartSet}>Refresh Analytics Charts</button>
        </div>
      </section>

      <section className="card chart-card">
        <h2 className="chart-title">Performance Analytics Charts</h2>
        <p className="muted">Trend and stability insights built from analytics trend and sessions history.</p>
        <ScreenState loading={chartState.loading} error={chartState.error} emptyMessage={chartEmptyMessage} />

        {!chartState.loading && !chartState.error && !chartEmptyMessage && (
          <div className="analytics-charts-grid">
            <article className="chart-card">
              <h3 className="chart-title">Accuracy Trend</h3>
              <EChartBase option={accuracyTrendOption} height={300} renderer="canvas" />
            </article>

            <article className="chart-card">
              <h3 className="chart-title">Pitch Error Trend</h3>
              <EChartBase option={pitchErrorOption} height={300} renderer="canvas" />
            </article>

            <article className="chart-card">
              <h3 className="chart-title">Timing Error Trend</h3>
              <EChartBase option={timingErrorOption} height={300} renderer="canvas" />
            </article>

            <article className="chart-card">
              <h3 className="chart-title">Instability Score</h3>
              <p className="muted">Weighted from inverse accuracy, pitch error, and timing error.</p>
              <EChartBase option={instabilityOption} height={300} renderer="canvas" />
            </article>
          </div>
        )}
      </section>
    </div>
  );
}
