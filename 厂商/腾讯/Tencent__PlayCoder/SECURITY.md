# Security

## Credential policy

- Do **not** commit API keys, GitHub tokens, or cloud credentials. Use environment variables or local-only config files that stay untracked (see [REPRO.md](REPRO.md)).
- Example configs in this repo use placeholders such as `YOUR_OPENAI_API_KEY`. Replace them locally; prefer `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and `GITHUB_TOKEN` in the environment.

## Historical secret in git history (GitHub PAT)

An automated pickaxe scan (`git log -p -S "ghp_"`) found that **`dataset/token.txt` once contained a real GitHub personal access token** in the initial import commit. The current working tree uses a placeholder, but **the old blob may still exist in history** until you rewrite it.

**You must:**

1. **Revoke** that PAT in GitHub (Settings → Developer settings → Personal access tokens), even if you believe it was already rotated.
2. **Purge or redact history** before a public release if this repository was ever pushed with that commit, or treat the token as permanently compromised.

### Option A: Redact with git-filter-repo (recommended if already pushed)

Install [git-filter-repo](https://github.com/newren/git-filter-repo), then from the repo root:

```bash
git filter-repo --replace-text tools/git-history-redact-patterns.txt --force
```

Review the result, then **force-push all branches** you care about (`git push --force --all` and tags if needed). Coordinate with anyone who has cloned the old history.

### Option B: New public repository

Create a **fresh** repository with only the current tree (no old `.git`), or export `git archive` and init a new repo. This avoids rewriting but loses commit history.

### Ongoing scanning

For deeper checks (OpenAI keys, AWS keys, etc.), run [TruffleHog](https://github.com/trufflesecurity/trufflehog) or enable GitHub **Secret scanning** on the organization/repository.

## Firebase / Google client keys

Vendor snapshots under `repos_TypeScript/biomes-game` and `repos_Javascript/win11React` load Firebase config from **environment variables** only. If you still use the original upstream Firebase projects, **rotate** any Web API keys that were previously committed elsewhere and enforce HTTP referrer / app restrictions in Google Cloud Console.

## Reporting

If you find a leaked secret in a fork or mirror, revoke the credential immediately and open an issue (or contact the maintainers privately) so the tree can be cleaned.
