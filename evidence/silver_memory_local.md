# Silver evidence: conversation memory (local)

History cap: 3 turns, each replayed answer truncated to 400 characters.

## Turn 1: Which client has the most projects?

- Route: sql
- SQL: `SELECT c.name, COUNT(p.id) AS project_count
FROM clients c
JOIN projects p ON p.client_id = c.id
GROUP BY c.id, c.name
ORDER BY project_count DESC
LIMIT 1;`
- Input tokens: 767

**Acme Corp** leads all clients with the most projects, currently having **3 projects** on record.

[Source: SQL Agent | SELECT c.name, COUNT(p.id) AS project_count
FROM clients c
JOIN projects p ON p.client_id = c.id
GROUP BY c.id, c.name
ORDER BY project_count DESC
LIMIT 1;]

## Turn 2 (with history): What about their contract value?

- Route: sql
- SQL: `SELECT c.name, c.contract_value
FROM clients c
JOIN projects p ON p.client_id = c.id
GROUP BY c.id, c.name
ORDER BY COUNT(p.id) DESC
LIMIT 1;`
- Input tokens: 985

Acme Corp, the client with the most projects, has a contract value of **$250,000**.

[Source: SQL Agent | SELECT c.name, c.contract_value
FROM clients c
JOIN projects p ON p.client_id = c.id
GROUP BY c.id, c.name
ORDER BY COUNT(p.id) DESC
LIMIT 1;]

## Same follow-up WITHOUT history (for comparison)

- SQL: `CANNOT_ANSWER`
- Input tokens: 610

The database does not contain the information needed to answer this.

[Source: SQL Agent | none]

## Cost impact

- Turn 2 with history used 985 input tokens vs 610 without history.
- Memory added 375 input tokens (61.5% more) for one replayed turn.