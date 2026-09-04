# Production cost baseline

Verified on 2026-09-04 against current official provider documentation. Currency
conversion and taxes are not included.

| Resource | Selected baseline | Recurring base | Included / notes |
| --- | --- | ---: | --- |
| GitHub | Pro personal account | USD 4/month | Required to protect branches in this private repository; the repository and CI already exist on Free |
| Vercel | Dedicated Mente do Brasil Pro team | USD 20/month | One deploying seat and USD 20 monthly usage credit; 1 TB Fast Data Transfer and 10 million Edge Requests listed as included allocations |
| Supabase | Dedicated Pro organization, one Micro production project | USD 25/month | USD 10 compute credit covers one Micro project; 8 GB database, 250 GB egress, daily backups retained 7 days |
| Registro.br | `mentedobrasil.com.br` | BRL 40/year | Official RDAP returned 404 on 2026-09-04, indicating no current registration record; availability must be reconfirmed at checkout |
| Contact forwarding | Cloudflare Email Routing, Free | USD 0 | Unlimited inbound routing to a verified destination; no custom-domain outbound SMTP |

Expected steady base: **USD 49/month + BRL 40/year**, before taxes and overages.
Temporary staging uses a second Supabase Micro project billed by active hour, at up to
approximately USD 10/month if retained for a full month. It must be deleted or paused
after launch. Vercel preview deployments are kept within the selected team.

Possible overages include Vercel compute/data transfer/edge requests beyond allocations
and credit, and Supabase compute, database disk, egress, storage, or other quota excess.
Provider usage notifications and a notification-only spend threshold must be enabled.
Do not configure an automatic action that can take the public service offline.

Explicitly excluded: PITR (currently starts around USD 100/month for seven days), paid
observability, extra compute, custom Supabase domain, IPv4 add-on, replicas, premium
firewall, and additional paid seats.

Official references:

- https://docs.github.com/en/get-started/learning-about-github/faq-about-changes-to-githubs-plans
- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- https://vercel.com/docs/plans/pro-plan
- https://vercel.com/docs/spend-management
- https://supabase.com/pricing
- https://supabase.com/docs/guides/platform/backups
- https://registro.br/ajuda/procedimentos-administrativos/pagamento-de-dominios/
- https://developers.cloudflare.com/email-service/platform/pricing/
