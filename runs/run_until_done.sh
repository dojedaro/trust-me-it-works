#!/usr/bin/env bash
# Rerun the experiment until every (variant, task, sample) trace exists. The runner resumes from
# saved traces, so each pass continues where the last one hit the free tier's rate limit.
for pass in $(seq 1 80); do
  .venv/Scripts/python -u -m trustme run --variants A,B,C,D,E,F --name v2b-2026-11-13 >> runs/v2b.log 2>&1
  n=$(find runs/v2b-2026-11-13 -name '*.json' | wc -l)
  echo "pass $pass: $n/432 traces" >> runs/v2b.log
  [ "$n" -ge 432 ] && exit 0
  sleep 600
done
