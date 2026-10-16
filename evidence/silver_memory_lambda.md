# Silver evidence: conversation memory (deployed on Lambda)

## Turn 1: Which client has the most projects?
- SQL: `SELECT c.name, COUNT(p.id) AS project_count
FROM clients c
JOIN projects p ON p.client_id = c.id
GROUP BY c.id, c.name
ORDER BY project_count DESC
LIMIT 1;`
- Input tokens: 767

**Acme Corp** leads all clients with **3 projects**, making them the most active client in the system.

[Source: SQL Agent | SELECT c.name, COUNT(p.id) AS project_count
FROM clients c
JOIN projects p ON p.client_id = c.id
GROUP BY c.id, c.name
ORDER BY project_count DESC
LIMIT 1;]

## Turn 2: What about their contract value? (history passed from Turn 1 response)
- History sent: 1 prior turn(s)
- SQL: `SELECT c.name, c.contract_value
FROM clients c
JOIN projects p ON p.client_id = c.id
GROUP BY c.id, c.name
ORDER BY COUNT(p.id) DESC
LIMIT 1;`
- Input tokens: 987

Acme Corp, the client with the most projects, has a contract value of **$250,000**.

[Source: SQL Agent | SELECT c.name, c.contract_value
FROM clients c
JOIN projects p ON p.client_id = c.id
GROUP BY c.id, c.name
ORDER BY COUNT(p.id) DESC
LIMIT 1;]

Turn 2 used +220 input tokens compared with Turn 1.