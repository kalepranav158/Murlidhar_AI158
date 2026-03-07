## Composite Score Formula

composite =
0.4 * accuracy +
0.3 * rhythm_index +
0.3 * technique_score

## Aggregation Method

- Last N = 20 sessions
- Weighted by recency
weight = 1 / (rank + 1)
