import type { AdaptiveCoachDrillCard } from "../types";

type AdaptiveCoachDrillCardsProps = {
  cards: AdaptiveCoachDrillCard[];
};

export default function AdaptiveCoachDrillCards({ cards }: AdaptiveCoachDrillCardsProps) {
  if (cards.length === 0) {
    return <p className="muted">No adaptive drill recommendations available for this attempt.</p>;
  }

  return (
    <div className="adaptive-coach-grid">
      {cards.map((card) => (
        <article key={`${card.title}-${card.value}`} className="adaptive-coach-card">
          <h4>{card.title}</h4>
          <p className="adaptive-coach-value">{card.value}</p>
          {card.detail && <p className="muted">{card.detail}</p>}
        </article>
      ))}
    </div>
  );
}
