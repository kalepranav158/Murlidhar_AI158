import fluteHistoryImage from "../assets/documentation/flute-history.svg";
import govardhanStoryImage from "../assets/documentation/govardhan-story.svg";

export default function DocumentationPage() {
  return (
    <div className="container documentation-page">
      <h1>Documentation</h1>
      <p className="muted">
        A cultural learning space with short notes on flute heritage and memorable stories of Shri Krishna.
      </p>

      <section className="card documentation-intro-card">
        <h2>Flute History</h2>
        <figure className="documentation-figure">
          <img src={fluteHistoryImage} alt="Stylized bansuri flute illustration" loading="lazy" />
          <figcaption>Traditional bansuri symbolism: breath to melody.</figcaption>
        </figure>
        <p>
          The bamboo flute (bansuri) is among the oldest melodic instruments in the Indian tradition.
          Its voice is simple, breath-driven, and close to human expression, which made it central to
          folk music, devotional music, and classical performances over centuries.
        </p>
        <p>
          In Indian aesthetics, the flute is often treated not just as an instrument but as a symbol of
          inner stillness, listening, and devotion.
        </p>
      </section>

      <section className="card documentation-stories-card">
        <div className="documentation-section-head">
          <h2>Shri Krishna Memorable Stories</h2>
          <span className="documentation-badge">Story Collection: Growing</span>
        </div>

        <p className="muted">
          This section will hold the full story collection. For now, one short story is included.
        </p>

        <article className="documentation-story-item">
          <h3>Story 1: Lifting Govardhan Hill</h3>
          <figure className="documentation-figure">
            <img
              src={govardhanStoryImage}
              alt="Illustration of Krishna sheltering people under Govardhan hill"
              loading="lazy"
            />
            <figcaption>A symbolic moment of protection, trust, and courage.</figcaption>
          </figure>
          <p>
            When heavy rains threatened the people of Vrindavan, young Krishna advised everyone to
            seek shelter near Govardhan. To protect them, he lifted the hill on his little finger and
            held it steady for seven days, giving safety to people, cows, and homes.
          </p>
          <p>
            The story is remembered as a lesson in courage, protection, and faith over fear.
          </p>
        </article>
      </section>
    </div>
  );
}
