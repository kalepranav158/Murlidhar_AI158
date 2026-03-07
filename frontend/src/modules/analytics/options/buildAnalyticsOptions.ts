import type { BaseChartOption } from "../../charts";

export type AnalyticsPoint = {
  label: string;
  value: number | null;
};

const categoriesFrom = (points: AnalyticsPoint[]): string[] => points.map((point) => point.label);
const valuesFrom = (points: AnalyticsPoint[]): Array<number | null> => points.map((point) => point.value);

const buildBaseLineOption = (
  points: AnalyticsPoint[],
  seriesName: string,
  yAxisLabel: string,
  color: string,
  yMin: number | undefined,
  yMax: number | undefined,
): BaseChartOption => {
  return {
    tooltip: {
      trigger: "axis",
    },
    legend: {
      data: [seriesName],
      bottom: 6,
      textStyle: {
        color: "#3f4b64",
      },
    },
    grid: {
      left: 36,
      right: 16,
      top: 28,
      bottom: 40,
      containLabel: true,
    },
    xAxis: {
      type: "category",
      data: categoriesFrom(points),
      axisLabel: {
        color: "#5d6473",
      },
      axisLine: {
        lineStyle: {
          color: "#c5cbdb",
        },
      },
    },
    yAxis: {
      type: "value",
      min: yMin,
      max: yMax,
      axisLabel: {
        color: "#5d6473",
        formatter: `{value}${yAxisLabel}`,
      },
      splitLine: {
        lineStyle: {
          color: "#e2e7f2",
        },
      },
    },
    series: [
      {
        name: seriesName,
        type: "line",
        smooth: true,
        lineStyle: {
          width: 2,
          color,
        },
        itemStyle: {
          color,
        },
        areaStyle: {
          opacity: 0.08,
          color,
        },
        data: valuesFrom(points),
      },
    ],
  };
};

export const buildAnalyticsAccuracyTrendOption = (
  points: AnalyticsPoint[],
): BaseChartOption => {
  return buildBaseLineOption(points, "Accuracy", "%", "#2563eb", 0, 100);
};

export const buildAnalyticsPitchErrorOption = (
  points: AnalyticsPoint[],
): BaseChartOption => {
  return buildBaseLineOption(points, "Pitch Error", " cents", "#dc2626", 0, undefined);
};

export const buildAnalyticsTimingErrorOption = (
  points: AnalyticsPoint[],
): BaseChartOption => {
  return buildBaseLineOption(points, "Timing Error", " sec", "#d97706", 0, undefined);
};

export const buildAnalyticsInstabilityOption = (
  points: AnalyticsPoint[],
): BaseChartOption => {
  const categories = categoriesFrom(points);
  const values = valuesFrom(points);

  return {
    tooltip: {
      trigger: "axis",
    },
    legend: {
      data: ["Instability Score", "Stable Ceiling", "Watch Ceiling"],
      bottom: 6,
      textStyle: {
        color: "#3f4b64",
      },
    },
    grid: {
      left: 36,
      right: 16,
      top: 28,
      bottom: 40,
      containLabel: true,
    },
    xAxis: {
      type: "category",
      data: categories,
      axisLabel: {
        color: "#5d6473",
      },
      axisLine: {
        lineStyle: {
          color: "#c5cbdb",
        },
      },
    },
    yAxis: {
      type: "value",
      min: 0,
      max: 100,
      axisLabel: {
        color: "#5d6473",
        formatter: "{value}%",
      },
      splitLine: {
        lineStyle: {
          color: "#e2e7f2",
        },
      },
    },
    series: [
      {
        name: "Instability Score",
        type: "line",
        smooth: true,
        lineStyle: {
          width: 2,
          color: "#0f766e",
        },
        itemStyle: {
          color: "#0f766e",
        },
        areaStyle: {
          opacity: 0.08,
          color: "#0f766e",
        },
        markArea: {
          silent: true,
          data: [
            [
              {
                name: "Stable",
                yAxis: 0,
                itemStyle: { color: "rgba(34, 197, 94, 0.10)" },
              },
              { yAxis: 30 },
            ],
            [
              {
                name: "Watch",
                yAxis: 30,
                itemStyle: { color: "rgba(245, 158, 11, 0.10)" },
              },
              { yAxis: 65 },
            ],
            [
              {
                name: "Critical",
                yAxis: 65,
                itemStyle: { color: "rgba(239, 68, 68, 0.10)" },
              },
              { yAxis: 100 },
            ],
          ],
        },
        data: values,
      },
      {
        name: "Stable Ceiling",
        type: "line",
        symbol: "none",
        lineStyle: {
          type: "dashed",
          width: 1,
          color: "#16a34a",
        },
        data: categories.map(() => 30),
      },
      {
        name: "Watch Ceiling",
        type: "line",
        symbol: "none",
        lineStyle: {
          type: "dashed",
          width: 1,
          color: "#d97706",
        },
        data: categories.map(() => 65),
      },
    ],
  };
};