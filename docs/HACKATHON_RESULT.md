# AMD ACT II Hackathon Result Record

## Final Observed Qualified Result

| Field | Recorded value |
|---|---|
| Project | OmniEdge RouteIQ — Local-First Intelligent Router |
| Team | OmniEdge RouteIQ |
| Track | Hybrid Token-Efficient Routing Agent |
| Final observed leaderboard position | 17th |
| Accuracy | 94.7% |
| Fireworks tokens | 3,100 |
| First submission | July 10, 2026 at 16:59 GMT+5:30 |
| Final recorded resubmission | July 12, 2026 at 20:47 GMT+5:30 |
| Final recorded score time | July 12, 2026 at 21:37 GMT+5:30 |
| Result status | Qualified and scored |

This file records the result observed by the team near the close of the hackathon. Organizer-side reviews, prize decisions, or later corrections should be appended as a new dated section rather than overwriting this record.

## Score Progression

| Recorded stage | Accuracy | Tokens | Notes |
|---|---:|---:|---|
| First scored qualified version | 84.2% | 12,531 | Established valid evaluator execution |
| Improved qualified version | 94.7% | 3,974 | Large accuracy and token improvement |
| Local-first lower-token attempt | 89.5% | 3,421 | Accuracy regression |
| Final protected version | 94.7% | 3,100 | Final observed 17th position |

## Improvement

From 12,531 to 3,100 Fireworks tokens:

```text
Token reduction = 9,431
Percentage reduction = 75.3%
```

The final score also improved from 84.2% to 94.7%.

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
- 18 of 19 locally correct in the test harness;
- zero Fireworks calls in that internal run;
- one remaining incorrect factual answer.

It was treated as an experiment rather than the protected final submission because official ranking depended first on correctness. The experiment should be used as a future R&D baseline, not presented as the final organizer score.

Private candidate references, hidden benchmark files, and non-public image identifiers must not be copied into public documentation.

## Closing Decision

With only a few hours remaining, the team preserved the 94.7% / 3,100-token qualified submission rather than risk:

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
