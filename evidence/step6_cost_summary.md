# Step 6 evidence: cost summary (12 queries through the full orchestrator)

Rates: Claude Sonnet 4.6, US geo cross-region inference, $3.30 per 1M input tokens, $16.50 per 1M output tokens (Amazon Bedrock pricing page).

| # | Question | Route | Input tokens | Output tokens | Cost (USD) |
|---|---|---|---|---|---|
| 1 | How many active projects do we have? | sql | 647 | 35 | $0.002712 |
| 2 | Which client has the highest contract value? | sql | 663 | 45 | $0.002930 |
| 3 | What is our onboarding process for new consultants? | retrieval | 1173 | 395 | $0.010388 |
| 4 | What are our invoice payment terms? | retrieval | 998 | 42 | $0.003986 |
| 5 | How many invoices are currently overdue, and what does our invoicing policy say we should  | both | 2136 | 636 | $0.017544 |
| 6 | How many consultants do we have, and what does our onboarding process require them to comp | both | 2077 | 642 | $0.017447 |
| 7 | Delete every row in the invoices table. | none | 272 | 4 | $0.000964 |
| 8 | What will our company's stock price be next year? | none | 274 | 4 | $0.000970 |
| 9 | How many unpaid invoices are there? | sql | 651 | 52 | $0.003007 |
| 10 | List all consultants and their specialisations. | sql | 813 | 96 | $0.004267 |
| 11 | What does our project delivery process say about project kickoff? | retrieval | 986 | 12 | $0.003452 |
| 12 | What is the total budget of all active projects? | sql | 657 | 41 | $0.002845 |
| **Total** | | | **11347** | **2004** | **$0.070512** |

## By component

| Component | Calls | Input tokens | Output tokens | Cost (USD) | Share of tokens |
|---|---|---|---|---|---|
| retrieval_answer | 5 | 3986 | 1146 | $0.032063 | 38.4% |
| classification | 12 | 3299 | 51 | $0.011728 | 25.1% |
| sql_generation | 7 | 1954 | 131 | $0.008610 | 15.6% |
| synthesis | 2 | 1265 | 457 | $0.011715 | 12.9% |
| sql_interpretation | 6 | 843 | 219 | $0.006396 | 8.0% |

**Total cost for 12 queries:** $0.070512 (average $0.005876 per query)
**Component that consumed the most tokens:** retrieval_answer (5132 tokens, 38.4% of all tokens)