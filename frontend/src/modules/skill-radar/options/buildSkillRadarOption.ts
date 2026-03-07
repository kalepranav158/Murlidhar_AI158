import type { BaseChartOption } from "../../charts";
import type { SkillRadarNormalized } from "../../../types/normalized";

const clamp01 = (value: number): number => {
  if (value < 0) {
    return 0;
  }

  if (value > 1) {
    return 1;
  }

  return value;
};

const toPercent = (value: number): number => {
  return Math.round(clamp01(value) * 1000) / 10;
};

export const buildSkillRadarOption = (radar: SkillRadarNormalized): BaseChartOption => {
  const values = [
    toPercent(radar.pitch),
    toPercent(radar.rhythm),
    toPercent(radar.technique),
    toPercent(radar.consistency),
    toPercent(radar.progress),
  ];

  return {
    tooltip: {
      trigger: "item",
    },
    legend: {
      bottom: 6,
      data: ["Skill Profile"],
      textStyle: {
        color: "#3f4b64",
      },
    },
    radar: {
      center: ["50%", "46%"],
      radius: "74%",
      splitNumber: 5,
      axisName: {
        color: "#3f4b64",
        fontSize: 12,
        fontWeight: 600,
        formatter: (name?: string) => (name ?? "").replace(/\s+/g, "\n"),
      },
      splitLine: {
        lineStyle: {
          color: "#d9deea",
        },
      },
      splitArea: {
        areaStyle: {
          color: ["#ffffff", "#f8faff"],
        },
      },
      axisLine: {
        lineStyle: {
          color: "#b7c0d6",
        },
      },
      indicator: [
        { name: "Pitch Control", max: 100 },
        { name: "Rhythm Stability", max: 100 },
        { name: "Technique Control", max: 100 },
        { name: "Consistency", max: 100 },
        { name: "Learning Progress", max: 100 },
      ],
    },
    series: [
      {
        type: "radar",
        symbol: "circle",
        symbolSize: 6,
        lineStyle: {
          width: 2,
          color: "#2563eb",
        },
        areaStyle: {
          color: "rgba(37, 99, 235, 0.24)",
        },
        itemStyle: {
          color: "#1d4ed8",
        },
        data: [
          {
            value: values,
            name: "Skill Profile",
          },
        ],
      },
    ],
  };
};
