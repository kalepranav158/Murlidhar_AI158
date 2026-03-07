import * as echarts from "echarts/core";
import { HeatmapChart, LineChart, RadarChart } from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  MarkAreaComponent,
  MarkLineComponent,
  RadarComponent,
  TooltipComponent,
  VisualMapComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

// Register only currently used chart primitives; add more modules when those views are implemented.
echarts.use([
  RadarChart,
  LineChart,
  HeatmapChart,
  RadarComponent,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  VisualMapComponent,
  MarkAreaComponent,
  MarkLineComponent,
  CanvasRenderer,
]);

export { echarts };
export type { EChartsOption } from "echarts";
