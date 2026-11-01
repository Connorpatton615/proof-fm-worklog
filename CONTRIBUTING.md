# Contributing

These are the pull-request rules this repository follows. They are short
because they are meant to be kept, not admired.

## One PR, one change

A pull request does one thing. A new endpoint, a bug fix, a doc update, a
dependency bump: each is its own PR. If the description needs the word
"also", split it.

Small PRs get reviewed the same day. Large ones get reviewed badly or not at
all.

## The title says what and why

The title is a sentence a reader can understand without opening the diff:

- `Add per-site summary endpoint so managers can see activity at a glance`
- `Reject photo filenames that contain a path`
- `Pin test dependencies so CI matches local runs`

Not: `Updates`, `Fix bug`, `WIP`.

## The description

Three short parts, in this order:

1. **What changed.** Two or three sentences in plain English. A manager
   should be able to read this part and know what they are getting.
2. **Why.** The problem or request that led to it.
3. **How it was tested.** What you ran and what you saw. "Tests pass" is a
   minimum, not an answer; name the case that proves the change.

If a reviewer needs to know something to review it well (a trade-off you
made, a thing you chose not to do), say it in the description, not in a
comment after they ask.

## Before asking for review

- `pytest` passes locally.
- CI is green on the PR. A red check means it is not ready; do not ask
  someone to review around it.
- New behaviour has a test. A bug fix has a test that failed before the fix.
- The README and runbook still tell the truth. If the change adds an
  endpoint, the endpoint table gains a row in the same PR.

## Commits

Small commits with messages that say what and why, in the same style as PR
titles. History is squashed on merge, so commits are for the reviewer's
benefit while the PR is open, not for posterity.

## Style

Follow what is already there. Standard library before a dependency. A
dependency only when it removes real code. No new framework or language
without a conversation first.
