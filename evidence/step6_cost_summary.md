# Step 6 evidence: cost summary (12 queries through the full orchestrator)

Rates: Claude Sonnet 4.6, US geo cross-region inference, $3.30 per 1M input tokens, $16.50 per 1M output tokens (Amazon Bedrock pricing page).

| # | Question | Route | Input tokens | Output tokens | Cost (USD) |
|---|---|---|---|---|---|
| 1 | How many active projects do we have? | sql | 716 | 35 | $0.002940 |
| 2 | Which client has the highest contract value? | sql | 732 | 45 | $0.003158 |
| 3 | What is our onboarding process for new consultants? | retrieval | 1251 | 381 | $0.010415 |
| 4 | What are our invoice payment terms? | retrieval | 1076 | 73 | $0.004755 |
| 5 | How many invoices are currently overdue, and what does our invoicing policy say we should  | both | 2189 | 632 | $0.017652 |
| 6 | How many consultants do we have, and what does our onboarding process require them to comp | both | 2303 | 606 | $0.017599 |
| 7 | Delete every row in the invoices table. | sql | 616 | 12 | $0.002230 |
| 8 | What will our company's stock price be next year? | none | 313 | 4 | $0.001099 |
| 9 | How many unpaid invoices are there? | sql | 720 | 52 | $0.003234 |
| 10 | List all consultants and their specialisations. | sql | 882 | 109 | $0.004710 |
| 11 | What does our project delivery process say about project kickoff? | retrieval | 1064 | 94 | $0.005062 |
| 12 | What is the total budget of all active projects? | sql | 732 | 45 | $0.003159 |
| **Total** | | | **12594** | **2088** | **$0.076013** |

## By component

| Component | Calls | Input tokens | Output tokens | Cost (USD) | Share of tokens |
|---|---|---|---|---|---|
| retrieval_answer | 5 | 4181 | 1138 | $0.032574 | 36.2% |
| classification | 12 | 3767 | 51 | $0.013273 | 26.0% |
| sql_generation | 8 | 2469 | 151 | $0.010639 | 17.8% |
| synthesis | 2 | 1210 | 457 | $0.011534 | 11.4% |
| sql_interpretation | 7 | 967 | 291 | $0.007993 | 8.6% |

**Total cost for 12 queries:** $0.076013 (average $0.006334 per query)
**Component that consumed the most tokens:** retrieval_answer (5319 tokens, 36.2% of all tokens)