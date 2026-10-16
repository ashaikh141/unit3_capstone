# Agent Evaluation, Monitoring & Tokenomics: Notes

## Part 2: Tracing
Trace 186b3f28 ("How many active projects do we have, and what's our onboarding process?") can be fully reconstructed from agent_decisions.jsonl without re-running it: routing chose "both" (keyword classifier, no Claude call); the SQL agent ran with validation PASSED and returned 1 row; the retrieval agent retrieved 5 chunks; synthesis used both results. The log correctly reads SQL validation status from the result's metadata. Reading a top-level "validation" key would have silently logged None.

## Part 3: Cost breakdown of a "both" query (trace 186b3f28)
| Component | Input | Output | Cost |
|---|---|---|---|
| SQL agent (generation + interpretation) | 1,244 | 76 | $0.0049 |
| Retrieval agent (answer generation) | 871 | 360 | $0.0080 |
| Synthesis | 548 | 482 | $0.0089 |
| **Total** | | | **$0.0218** (~$21.76 per 1,000 queries) |

The synthesis step was the most expensive component even though it had the fewest input tokens, because output tokens cost five times more than input tokens ($0.015 vs $0.003 per 1K) and synthesis writes long, formatted answers. This was surprising: I expected the SQL agent to be most expensive because it sends the entire ~1,100-token schema context on every call, but input tokens are cheap.

## 10-query cost summary
Total: $0.1375 for 10 queries (average $0.0137 per query, ~$13.75 per 1,000 queries).

| Component | Tokens | Share of tokens | Cost | Share of cost |
|---|---|---|---|---|
| Retrieval agent | 10,886 | 43% | $0.0532 | 39% |
| Synthesis | 6,113 | 24% | $0.0519 | 38% |
| SQL agent | 8,277 | 33% | $0.0324 | 24% |

The retrieval agent consumed the most tokens, mainly because neighbor expansion sends up to 8 chunks per question. Synthesis is far more expensive per token than either agent because it is output-heavy.

## Part 4: Estimating the cost of growth (10 → 10,000 documents)
Token cost does not grow with the number of documents, because the retrieval agent only ever sends its top-k chunks (5, plus up to 3 neighbors) to Claude, whether the index holds 32 chunks or 30,000. Each chunk is about 150–200 tokens, so retrieval input stays around 800–1,750 tokens per question. What does grow is competition: going from 12 to 32 chunks already pushed a needed onboarding chunk out of the top 3 and later the top 5. At 10,000 documents I would expect to need a larger top_k or more neighbor expansion to keep answers complete. Cost grows linearly with top_k: each extra chunk adds roughly 200 input tokens, about $0.0006 per query or $0.60 per 1,000 queries. So the real relationship is cost ∝ top_k × chunk size, and corpus growth raises cost indirectly by forcing a larger top_k. On the SQL side, cost is bounded by the fixed schema context and by passing at most 50 result rows to the interpretation step.

## Part 5: Orchestration efficiency audit
1. **Workers only run when routed.** The log confirms "ran": false for skipped agents, so no tokens are spent on agents the route doesn't need.
2. **The keyword router costs nothing but misroutes.** "What is the total invoiced amount for each client?" was routed to both agents because "what is" is a document keyword, wasting a retrieval call and a larger synthesis (over half that query's $0.0166). A Claude-based classifier would cost a few hundred tokens per question but avoid misroutes like this; for my traffic, removing "what is" from the keyword list is the cheaper fix.
3. **Unanswerable questions are expensive.** "What's the weather like today?" matched no keywords and defaulted to retrieval, spending 1,749 input tokens on 8 irrelevant chunks and then 199 output tokens in synthesis to say it couldn't answer, $0.0088 for nothing. Skipping synthesis when no agent found an answer would remove most of this cost.
4. **Synthesis on single-agent routes is redundant.** For the six single-route questions, synthesis re-summarized an answer that was already complete, about 19% of total spend. Returning the agent's answer directly when only one agent ran would cut that, at the cost of less consistent formatting.
5. **Compound questions are sent whole to each agent.** For "How many consultants are Managers, and what is the billable hours target for a Manager?", the SQL agent returned CANNOT_ANSWER because half the question isn't in the database, so the final answer lost the Manager count entirely. Splitting the question into one sub-question per agent would fix both the wasted call and the incomplete answer.
6. **The grounding check produced a false alarm** on the cloud migration question, most likely because the citation omitted the sample-documents/ folder prefix. Comparing file names without folders fixes it.