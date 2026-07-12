# Team Ownership and Handoff

Updated after the AMD Developer Hackathon: ACT II closing-stage result.

## Operating Principle

Technical ownership, contribution history, and ongoing maintenance are recorded separately. New assignments do not rewrite who completed earlier work.

## Current Team Structure

### Rama Chandra — Founder and Product/Architecture Lead

Owns:

- product direction;
- routing architecture;
- benchmark strategy;
- deterministic and model-routing decisions;
- backend and Docker scoring decisions;
- final technical review;
- release approval;
- partnerships, pilot direction, and external representation.

Rama remains the final approver for benchmark claims, architecture changes, and public technical statements.

### Nabothan — Frontend and UI Contributor

Owns:

- Command Nexus frontend;
- route visualization;
- dashboard layout and usability;
- frontend API integration quality;
- responsive and presentation-ready UI;
- frontend screenshots and demo presentation polish.

### Rameen — QA, Product, and Documentation Contributor

Owns:

- functional QA;
- route and simulation testing;
- demo-flow review;
- submission-story support;
- testing documentation;
- backend simulation validation;
- review of reproduction steps and public QA claims.

### Priyanka Pandey — Project Operations and Documentation Support

Owns:

- root README upkeep;
- documentation index;
- dated benchmark and leaderboard evidence;
- release notes and changelog summaries;
- verification of public links;
- project archive organization;
- weekly project-status summaries;
- issue and pull-request status summaries;
- coordination of post-hackathon documentation.

Priyanka joined the support workstream near the closing stage. Her current role is operational and documentation-focused; it does not retroactively attribute core scoring-agent or frontend implementation.

## Founder Work Reassigned to Priyanka

| Previously handled mainly by Rama | New owner | Approval |
|---|---|---|
| Root README maintenance | Priyanka | Rama approves technical claims |
| Benchmark screenshot and result log | Priyanka | Rama confirms publishable result |
| Release-note drafting | Priyanka | Rama approves release status |
| Demo/API/public-link checks | Priyanka | Technical fixes go to Rama or Nabothan |
| Submission and pitch-file archive | Priyanka | Team supplies source files |
| Weekly status summary | Priyanka | Rama sets priorities |
| Open issue and PR summary | Priyanka | Rama reviews technical closure |

## Handoff Workflow

1. Priyanka collects the latest score, image label, branch, commit, screenshots, and notes.
2. She marks each item as one of:
   - official evaluator result;
   - internal benchmark;
   - experimental candidate;
   - product demo result.
3. Rameen checks the reproduction and QA wording.
4. Nabothan checks frontend links and screenshots when relevant.
5. Rama approves technical claims.
6. Priyanka updates the README, result log, release notes, and archive.
7. The team commits documentation separately from agent-code changes whenever possible.

## Protected Boundaries

Priyanka should not independently:

- change routing thresholds;
- modify scoring-agent logic;
- replace Docker entrypoints;
- publish hidden or private image references;
- claim an internal score as an official score;
- resubmit the hackathon image;
- merge architecture changes without Rama's approval.

These boundaries keep documentation ownership meaningful without creating release risk.
