# Baseline and SLO Gate

## SLO Targets

- Read API (cache hit): p95 < 120ms
- Read API (cache miss): p95 < 300ms
- Write API: p95 < 500ms
- Error rate: < 0.1%

## Baseline Capture Checklist

1. Start stack with `docker-compose.yml` and v2 endpoints.
2. Run k6 scenario in `tests/load/k6_baseline.js`.
3. Collect `/metrics`, app logs, and docker stats.
4. Record values in the template below.

## Baseline Template

| Date | Environment | RPS | p50 | p95 | Error Rate | CPU | Memory |
| ---- | ----------- | --- | --- | --- | ---------- | --- | ------ |
| TBD  | compose     | TBD | TBD | TBD | TBD        | TBD | TBD    |
