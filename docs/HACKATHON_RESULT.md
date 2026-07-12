# AMD ACT II Hackathon Result Record

## Final Observed Qualified Result

| Field | Recorded value |
|---|---|
| Project | OmniEdge RouteIQ — Local-First Intelligent Router |
| Team | OmniEdge RouteIQ |
| Track | Hybrid Token-Efficient Routing Agent |
| Final observed leaderboard position | 15th |
| Accuracy | 100.0% |
| Fireworks tokens | 3,296 |
| First submission | July 10, 2026 at 16:59 GMT+5:30 |
| Final recorded resubmission | July 12, 2026 at 22:36 GMT+5:30 |
| Final recorded score time | July 13, 2026 at 00:18 GMT+5:30 |
| Result status | Qualified and scored |

This file records the result observed by the team near the close of the hackathon. Organizer-side reviews, prize decisions, or later corrections should be appended as a new dated section rather than overwriting this record.

## Score Progression

| Recorded stage | Accuracy | Tokens | Notes |
|---|---:|---:|---|
| First scored qualified version | 84.2% | 12,531 | Established valid evaluator execution |
| Improved qualified version | 94.7% | 3,974 | Large accuracy and token improvement |
| Local-first lower-token attempt | 89.5% | 3,421 | Accuracy regression |
| Final scored version | 100.0% | 3,296 | Final observed 15th position; 19 of 19 correct |

## Improvement

From 12,531 to 3,296 Fireworks tokens:

```text
Token reduction = 9,235
Percentage reduction = 73.7%
```

The final score also improved from 84.2% to 100.0%.

## Infrastructure Events

Several submission checks displayed organizer-side `INFRA_ERROR` states during the hackathon. The team continued development while preserving known working images and resaving submissions when appropriate.

Documentation rule:

- Record an infrastructure error as an evaluator event.
- Do not automatically classify it as an application defect.
- Check whether the same image previously scored.
- Reproduce locally where possible.
- Preserve the last known qualified result before changing the image.

## Experimental v1.8.1 Note

A v1.8.1 single-pass local-only candidate completed an internal 19-task benchmark with:

- 19 results written;
- 18 of 19 locally correct in the earlier internal test harness;
- zero Fireworks calls in that internal run;
- one remaining incorrect factual answer.

That internal run was treated as an experiment because official ranking depended first on correctness. The later evaluator run reached 100.0% accuracy with 3,296 tokens and became the final protected benchmark result.

Private candidate references, hidden benchmark files, and non-public image identifiers must not be copied into public documentation.

## Closing Decision

After reaching 100.0% accuracy with 3,296 tokens, the team preserved the qualified submission rather than risk:

- lower accuracy;
- output-schema regression;
- missing tasks;
- runtime failure;
- timeout;
- a new infrastructure error;
- loss of the existing leaderboard position.

## Record Ownership

Primary record maintainer: **Priyanka Pandey**

Approval of technical and benchmark claims: **Rama Chandra**

QA/reproduction review: **Rameen**
