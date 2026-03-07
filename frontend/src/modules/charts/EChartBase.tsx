import ReactEChartsCore from "echarts-for-react/lib/core";
import { echarts } from "./echarts";
import type { BaseChartOption, ChartEvents, ChartHeight, ChartRenderer } from "./types";

type EChartBaseProps = {
  option: BaseChartOption | null;
  loading?: boolean;
  height?: ChartHeight;
  renderer?: ChartRenderer;
  className?: string;
  onEvents?: ChartEvents;
};

export default function EChartBase({
  option,
  loading = false,
  height = 320,
  renderer = "canvas",
  className,
  onEvents,
}: EChartBaseProps) {
  const chartClassName = className ? `chart-wrap ${className}` : "chart-wrap";

  if (!option) {
    return (
      <div className={chartClassName}>
        <p className="muted">No chart data available.</p>
      </div>
    );
  }

  return (
    <div className={chartClassName}>
      <ReactEChartsCore
        echarts={echarts}
        option={option}
        notMerge={true}
        lazyUpdate={true}
        showLoading={loading}
        onEvents={onEvents}
        opts={{ renderer }}
        style={{ height, width: "100%" }}
      />
    </div>
  );
}
