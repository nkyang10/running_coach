# AI Private Coach — Commercial Model

> Basic coaching is ALWAYS free.
> Premium is for depth, analysis, and convenience — not essential features.

---

## Pricing Philosophy

```
Core principle: The free tier must be genuinely useful on its own.

Free users = product validation + word-of-mouth
Pro users = revenue
Enterprise = stability

No feature should be paywalled if it's essential for training.
```

---

## Tier Structure

| Feature | Free 🆓 | Pro ($9.99/mo) | Enterprise ($49.99/mo) |
|---|---|---|---|
| Personalized training plans | ✅ Unlimited | ✅ Unlimited | ✅ Unlimited |
| Session logging & tracking | ✅ Unlimited | ✅ Unlimited | ✅ Unlimited |
| Basic progress tracking | ✅ 3 metrics | ✅ Unlimited metrics | ✅ Unlimited metrics |
| Training history (sessions) | ✅ Last 30 days | ✅ Full history | ✅ Full history |
| Injury-aware modifications | ✅ | ✅ | ✅ |
| AI coaching responses | ✅ Basic | ✅ Advanced | ✅ Advanced |
| **---** | **---** | **---** | **---** |
| Progress charts & insights | ❌ | ✅ Weekly PDF report | ✅ Custom dashboard |
| Advanced analytics | ❌ | ✅ Plateau detection, volume trends, fatigue analysis | ✅ Same + custom metrics |
| Program library access | ❌ | ✅ Full library (12+ programs) | ✅ Full library + custom programs |
| Deload scheduling | ❌ | ✅ Auto-suggested | ✅ Auto + manual override |
| Priority support | ❌ | ✅ Email (24h) | ✅ Telegram direct (4h) |
| **---** | **---** | **---** | **---** |
| Multi-user (gym/team) | ❌ | ❌ | ✅ Up to 50 users |
| White-label bot | ❌ | ❌ | ✅ Custom branding |
| API access | ❌ | ❌ | ✅ Webhook API |
| Custom knowledge base | ❌ | ❌ | ✅ Custom curriculum |

---

## Payment Infrastructure

```yaml
Provider: Stripe (free to start, 2.9% + $0.30/transaction)
Package: python-stripe
Billing: Monthly subscription, cancel anytime
Free tier: No payment info needed

Implementation:
  /subscribe → Stripe Checkout link
  /cancel → Confirm cancellation
  Stripe webhook → update user.tier in SQLite
  No expiry check on free tier (truly free forever)
```

---

## Monetization Strategy

### Phase 1: Launch (Month 1-3)
- Free tier only
- Build user base, collect feedback
- Target: 100 active users

### Phase 2: Premium Launch (Month 4)
- Introduce Pro tier ($9.99/mo)
- Existing free users get 1 month Pro free
- Target: 10% conversion rate

### Phase 3: Enterprise (Month 7+)
- Gym / personal trainer partnerships
- Custom knowledge base for each gym
- Target: 5 enterprise clients

---

## Revenue Projection

```yaml
Conservative estimate:
  100 free users × 10% conversion × $9.99  = $99.90/mo
  5 enterprise × $49.99                     = $249.95/mo
  Total: $349.85/mo

Optimistic estimate:
  500 free users × 15% conversion × $9.99  = $749.25/mo
  15 enterprise × $49.99                     = $749.85/mo
  Total: $1,499.10/mo
```

---

## API Cost Estimation

```yaml
Per-user per-month:
  Plan generation:      30 days × 1 plan × ~2K tokens     = ~60K tokens
  Log analysis:         30 days × 1 log × ~1K tokens      = ~30K tokens
  Status/progress:      10 calls × ~1K tokens              = ~10K tokens
  Total per user:       ~100K tokens/month

  GPT-4o-mini cost:     $0.15/M input × 70K + $0.60/M output × 30K
                       = ~$0.03/user/month

Cost for 100 free users:           ~$3.00/mo
Cost for 10 Pro users:             ~$0.30/mo
Cost for 5 Enterprise users:       ~$0.15/mo (lower usage)

Total API cost:                    ~$3.45/mo
Total infra cost (existing VM):    $0

Profit at conservative estimate:   ~$346/mo
Profit at optimistic estimate:     ~$1,496/mo
```

---

## Implementation Priority

```yaml
Phase 1 (Launch):
  - No billing system
  - Everyone is free tier
  - Focus on user retention

Phase 2 (Premium):  
  - Integrate Stripe
  - /subscribe command
  - Feature gating by tier
  - One month free for existing users

Phase 3 (Enterprise):
  - Multi-user management
  - White-label config
  - Custom knowledge base per client
```

---

## Ethical Principles

1. **Free tier is genuinely useful.** Not a crippled demo.
2. **No data lock-in.** Users can export all their data anytime.
3. **No dark patterns.** Cancel anytime, no questions asked.
4. **Injury safety is never paywalled.** Safety features are always free.
5. **Privacy by design.** User data belongs to the user, not us.
