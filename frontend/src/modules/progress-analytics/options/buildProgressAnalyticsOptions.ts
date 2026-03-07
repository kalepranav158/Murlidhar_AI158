import type { BaseChartOption } from "../../charts";

export type ProgressAnalyticsPoint = {
  label: string;
  accuracy: number | null;
  pitch: number | null;
  rhythm: number | null;
  technique: number | null;
  composite: number | null;
};

const buildCategories = (points: ProgressAnalyticsPoint[]): string[] => {
  return points.map((point) => point.label);
};

const toSeriesData = (points: ProgressAnalyticsPoint[], selector: (point: ProgressAnalyticsPoint) => number | null) => {
  return points.map((point) => selector(point));
};

export const buildSkillImprovementOption = (points: ProgressAnalyticsPoint[]): BaseChartOption => {
  const categories = buildCategories(points);

  return {
    tooltip: {
      trigger: "axis",
    },
    legend: {
      data: ["Pitch", "Rhythm", "Technique", "Composite"],
      bottom: 6,
      textStyle: {
        color: "#3f4b64",
      },
    },
    grid: {
      left: 32,
      right: 16,
      top: 28,
      bottom: 42,
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
        formatter: "{value}%",
        color: "#5d6473",
      },
      splitLine: {
        lineStyle: {
          color: "#e2e7f2",
        },
      },
    },
    series: [
      {
        name: "Pitch",
        type: "line",
        smooth: true,
        data: toSeriesData(points, (point) => point.pitch),
      },
      {
        name: "Rhythm",
        type: "line",
        smooth: true,
        data: toSeriesData(points, (point) => point.rhythm),
      },
      {
        name: "Technique",
        type: "line",
        smooth: true,
        data: toSeriesData(points, (point) => point.technique),
      },
      {
        name: "Composite",
        type: "line",
        smooth: true,
        data: toSeriesData(points, (point) => point.composite),
      },
    ],
  };
};

export const buildCompositeTrendOption = (points: ProgressAnalyticsPoint[]): BaseChartOption => {
  const categories = buildCategories(points);

  return {
    tooltip: {
      trigger: "axis",
    },
    legend: {
      data: ["Accuracy", "Composite"],
      bottom: 6,
      textStyle: {
        color: "#3f4b64",
      },
    },
    grid: {
      left: 32,
      right: 16,
      top: 28,
      bottom: 42,
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
        formatter: "{value}%",
        color: "#5d6473",
      },
      splitLine: {
        lineStyle: {
          color: "#e2e7f2",
        },
      },
    },
    series: [
      {
        name: "Accuracy",
        type: "line",
        smooth: true,
        areaStyle: {
          opacity: 0.12,
        },
        data: toSeriesData(points, (point) => point.accuracy),
      },
      {
        name: "Composite",
        type: "line",
        smooth: true,
        data: toSeriesData(points, (point) => point.composite),
      },
    ],
  };
};
