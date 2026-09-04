# Public launch checklist

- [ ] CI passes on the exact production candidate commit.
- [ ] GitHub repository is private; history/worktree secret scan passes.
- [ ] Branch protection requires critical CI without mandatory second reviewer.
- [ ] Dedicated Vercel Pro team and separate web/API projects exist in `gru1`.
- [ ] Dedicated Supabase Pro production and temporary staging projects exist in `sa-east-1`.
- [ ] SSL enforcement and client `verify-full` are verified with the provider CA.
- [ ] Runtime role is read-only; `anon` and `authenticated` have no application data access.
- [ ] Staging DB, external routes/API, security, visual, mobile, accessibility, and low-volume performance gates pass.
- [ ] Production DB rebuild and all scientific/content identity gates pass.
- [ ] Daily provider backup exists; isolated cloud restore/rebuild drill passes with RPO/RTO recorded.
- [ ] Geometry gate is `PASS_EXACT_SOURCE_PROVENANCE`; visible IBGE attribution is present.
- [ ] Domain ownership, DNS, HTTPS, apex canonicalization, `www`, and HTTP redirects pass.
- [ ] Contact forwarding is monitored and a real delivery/reply test passes.
- [ ] `security.txt`, privacy page, canonical URLs, Open Graph, robots, and sitemap pass.
- [ ] Direct backend denies unauthenticated access and docs/OpenAPI; web facade remains functional.
- [ ] `/healthz`, `/readyz`, monitors, provider logs, and notification-only spend alerts pass.
- [ ] Live ZIP is exactly 914294 bytes with the locked SHA-256.
- [ ] Production external E2E and final visual QA pass on 375, 390, 430, and desktop viewports.
- [ ] `public_release_status` changes to `RELEASED` only after every prior item passes.
- [ ] Exact launch commit is tagged `v1.0.0`; final audit ZIP is verified and uploaded to Drive.

The code repository does not contain the complete scientific source artifact store. CI
checks code, contracts, committed public artifacts, and static scientific locks; a full
scientific rebuild remains a controlled release process using the locked external
artifacts.
