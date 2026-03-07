import { useMemo } from "react";
import { EChartBase } from "../../charts";
import type { ChartRenderer } from "../../charts";
import type { SkillRadarNormalized } from "../../../types/normalized";
import { buildSkillRadarOption } from "../options/buildSkillRadarOption";

type SkillRadarEChartProps = {
  radar: SkillRadarNormalized;
  loading?: boolean;
  renderer?: ChartRenderer;
};

export default function SkillRadarEChart({
  radar,
  loading = false,
  renderer = "canvas",
}: SkillRadarEChartProps) {
  const option = useMemo(() => buildSkillRadarOption(radar), [radar]);

  return (
    <EChartBase
      option={option}
      loading={loading}
      height={460}
      renderer={renderer}
      className="skill-radar-echart-wrap"
    />
  );
}
