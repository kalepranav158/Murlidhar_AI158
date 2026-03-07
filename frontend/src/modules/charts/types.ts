import type { EChartsOption } from "./echarts";

export type ChartRenderer = "canvas" | "svg";
export type ChartHeight = number | string;

export type ChartEventHandler = (params: unknown, chart: unknown) => void;
export type ChartEvents = Record<string, ChartEventHandler>;

export type BaseChartOption = EChartsOption;
