# Rollback Plan (v1.0.19)

## Trigger Conditions
- GitHub Actions release workflow fails after tag push.
- Built artifacts fail smoke validation on clean Windows VM.
- Critical regression is reported post-release.

## Rollback Steps
1. Stop distribution of `v1.0.19` artifacts in the GitHub release page.
2. Repoint documentation/download links to the previous stable release `v1.0.18`.
3. If `v1.0.19` tag is already published, create hotfix from `v1.0.18` commit and release as `v1.0.20` with rollback note.
4. Announce rollback reason and mitigation in release notes.

## Recovery Checks
- Confirm `v1.0.18` artifacts are downloadable and executable.
- Run `python quality/verify_release.py --include-flake8` on rollback/hotfix commit before re-release.
