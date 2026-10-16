SCHEMA_CONTEXT = """
PostgreSQL database for a consulting firm. Four tables:

clients: client organizations the firm works for (one row per client)
- id (integer, primary key)
- name (text, required): client organization name, e.g. 'Acme Corp', 'Beta Financial'
- industry (text): one of 'Retail', 'Finance', 'Healthcare', 'Technology', 'Manufacturing', 'Energy'
- region (text): one of 'North', 'South', 'East', 'West'
- contract_value (numeric): total contract value with the client, in USD
- created_date (date): date the client relationship began

projects: consulting projects (each belongs to exactly one client)
- id (integer, primary key)
- client_id (integer, foreign key -> clients.id)
- name (text, required): project name, e.g. 'Acme Inventory Forecasting'
- status (text): one of 'active', 'completed', 'on_hold' (always lowercase)
- start_date (date)
- end_date (date): NULL if not yet set
- budget (numeric): project budget, in USD

consultants: firm staff (each assigned to at most one project)
- id (integer, primary key)
- name (text, required): full name, e.g. 'Priya Sharma'
- grade (text): one of 'Analyst', 'Consultant', 'Senior Consultant', 'Manager', 'Partner'
- specialisation (text): main skill area, e.g. 'Data Engineering', 'Cloud', 'Strategy'
- project_id (integer, foreign key -> projects.id): NULL if unassigned
- billable_hours (numeric): billable hours logged this year

invoices: bills sent for project work (each belongs to one project)
- id (integer, primary key)
- project_id (integer, foreign key -> projects.id)
- amount (numeric): invoice amount, in USD
- status (text): one of 'paid', 'pending', 'overdue' (always lowercase)
- due_date (date)
- paid_date (date): NULL unless status = 'paid'

Relationships and join rules:
- clients.id = projects.client_id
- projects.id = consultants.project_id
- projects.id = invoices.project_id
- Invoices have no client_id. To get invoices per client, join invoices -> projects -> clients.
- Never join consultants and invoices in the same query when summing amounts or hours:
  a project with 2 consultants and 2 invoices produces 4 rows and double-counts.
- contract_value (on clients) and budget (on projects) are different numbers. Do not mix them up.
- When filtering by a name, use ILIKE so capitalization does not matter, e.g. name ILIKE 'acme corp'.

Business definitions (use these when a question is vague):
- "best", "top", or "most productive" consultant = highest billable_hours.
- "biggest", "largest", or "most valuable" client = highest contract_value.
- "recent" or "recently" = within the last 12 months: date_column >= CURRENT_DATE - INTERVAL '12 months'.
- "this quarter" = date_column >= date_trunc('quarter', CURRENT_DATE).
- Two tables have a status column, with different meanings:
  projects.status is the state of the work ('active', 'completed', 'on_hold');
  invoices.status is the state of a payment ('paid', 'pending', 'overdue').
  'pending', 'paid', and 'overdue' always refer to invoices; 'active', 'completed', and 'on_hold' always refer to projects.
  Clients have no status. "The status of a client" means the status of each of that client's projects.

Safety rules:
- Only query the four tables above. Never query information_schema, pg_catalog, or any system table.
- If a question asks for "everything" or all records with no filter, query only the single most relevant table and add LIMIT 50.
"""