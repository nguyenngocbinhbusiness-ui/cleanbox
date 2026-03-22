# Rollback Plan: v1.0.18

## Trigger Conditions
- Error rate or crash rate increases above 5% after release
- Release artifact fails smoke test on clean Windows host
- Data-loss or cleanup misbehavior reported by users

## Steps
1. Delete or mark the `v1.0.18` GitHub release as pre-release/rolled back
2. Re-tag previous stable commit and publish `v1.0.17` artifacts again
3. DB rollback: N/A (desktop app, no schema migration)
4. Notify stakeholders in release channel and issue tracker

## Verification
- [ ] Previous stable version artifacts are available
- [ ] Portable EXE and setup installer launch correctly
- [ ] No data loss reported from rollback path

## Post-Rollback
- [ ] Open incident with root cause analysis
- [ ] Create fix branch from failed release commit
