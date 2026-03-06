# Gray Release Playbook

## Traffic Ramp

1. Shift 5% traffic to `/api/v2`
2. Observe for 30 minutes
3. Shift 25% traffic
4. Observe for 30 minutes
5. Shift 50% traffic
6. Observe for 30 minutes
7. Shift 100% traffic

## Gate Conditions

- Error rate < 0.1%
- Read p95 < 300ms
- Write p95 < 500ms
- No sustained Mongo/Redis dependency alert

## Rollback Conditions

- Error rate >= 0.1% for 5 minutes
- p95 latency exceeds SLO for 10 minutes
- Mongo replica set instability
- Redis unavailability causes user-visible failures

## Rollback Action

- Use Traefik service weight to route all traffic back to v1.
- Keep v2 alive for diagnostics in read-only mode when possible.
- Capture incident timeline and metrics snapshot.
