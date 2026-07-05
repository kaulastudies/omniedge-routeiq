#!/bin/bash

mkdir -p audit/closed-issues

echo "Fetching closed issues..."

gh issue list \
  --state closed \
  --limit 100 \
  --json number,title,state,author,assignees,labels,closedAt,url \
  > audit/closed-issues-list.json

jq -r '.[].number' audit/closed-issues-list.json | while read issue; do
  echo "Downloading issue #$issue..."
  gh issue view "$issue" --comments \
    --json number,title,state,author,assignees,labels,body,comments,closedAt,url \
    > "audit/closed-issues/issue-$issue.json"
done

echo "# OmniEdge RouteIQ Closed Issues Audit" > audit/closed-issues-report.md
echo "" >> audit/closed-issues-report.md

for file in audit/closed-issues/*.json; do
  jq -r '
  "## Issue #\(.number): \(.title)",
  "",
  "- State: \(.state)",
  "- Author: @" + .author.login,
  "- Closed At: \(.closedAt)",
  "- URL: \(.url)",
  "",
  "### Body",
  (.body // "No body"),
  "",
  "### Comments",
  (.comments[]? | "- @" + .author.login + ": " + (.body | gsub("\n"; " "))),
  "",
  "---",
  ""
  ' "$file" >> audit/closed-issues-report.md
done

echo "Done. Report created:"
echo "audit/closed-issues-report.md"
