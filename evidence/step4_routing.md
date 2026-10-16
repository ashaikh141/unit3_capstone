# Step 4 evidence: orchestrator routing

## SQL-only

```json
{
  "question": "How many active projects do we have?",
  "route": "sql",
  "sql_agent_ran": true,
  "retrieval_agent_ran": false,
  "sql_result": {
    "success": true,
    "answer": "There are **6 active projects** in the system.",
    "sources": [
      "SELECT COUNT(*) FROM projects WHERE status = 'active';"
    ],
    "metadata": {
      "tool": "sql_agent",
      "sql_validation": "PASSED",
      "sql": "SELECT COUNT(*) FROM projects WHERE status = 'active';",
      "validation_reason": "Single read-only SELECT",
      "row_count": 1,
      "latency_s": 1.45
    }
  },
  "retrieval_result": null,
  "final_answer": "There are **6 active projects** in the system.\n\n[Source: SQL Agent | SELECT COUNT(*) FROM projects WHERE status = 'active';]"
}
```

## Retrieval-only

```json
{
  "question": "What is our onboarding process for new consultants?",
  "route": "retrieval",
  "sql_agent_ran": false,
  "retrieval_agent_ran": true,
  "sql_result": null,
  "retrieval_result": {
    "success": true,
    "answer": "## Consultant Onboarding Process\n\nBased on our onboarding documentation, all new consultants follow the same process regardless of grade [onboarding_process.pdf]:\n\n### Before Day One\n- **Welcome pack** is sent by People Operations one week before the start date\n- **IT setup** is completed: laptop shipped, and email, timesheet, and project tool accounts created\n- Each new hire is **assigned an onboarding buddy** at the same grade or one grade above [onboarding_process.pdf]\n\n### Week One\n- **Day 1:** Orientation, benefits enrollment, and a meeting with the onboarding buddy\n- **Day 2:** Mandatory data security training *(must be completed before accessing any client data)*\n- **Days 3\u20135:** Delivery methodology, timesheet and billable hours rules, and expense policy\n- **New Managers and Partners** also meet with the Managing Partner during week one [onboarding_process.pdf]\n\n### Project Assignment\n- New consultants are assigned to their first project **by the end of week two**\n- Analysts and Consultants join an **existing active project team** and cannot be the sole consultant on a project during their **first 90 days** [onboarding_process.pdf]\n\n### Check-ins & Completion\n- The manager holds formal check-ins at **30, 60, and 90 days**\n- At the 90-day check-in, the manager confirms the consultant is on track for their billable hours target\n- Onboarding is **officially complete** when the 90-day check-in is signed off [onboarding_process.pdf]",
    "sources": [
      "onboarding_process.pdf"
    ],
    "metadata": {
      "tool": "retrieval_agent",
      "chunk_scores": [
        {
          "doc": "onboarding_process.pdf",
          "score": 0.8782
        },
        {
          "doc": "onboarding_process.pdf",
          "score": 0.7684
        },
        {
          "doc": "project_delivery_methodology.pdf",
          "score": 0.7446
        },
        {
          "doc": "consultant_grades_and_utilization.pdf",
          "score": 0.7408
        }
      ],
      "grounded": true,
      "cited_docs": [
        "onboarding_process.pdf"
      ],
      "latency_s": 3.33
    }
  },
  "final_answer": "## Consultant Onboarding Process\n\nBased on our onboarding documentation, all new consultants follow the same process regardless of grade [onboarding_process.pdf]:\n\n### Before Day One\n- **Welcome pack** is sent by People Operations one week before the start date\n- **IT setup** is completed: laptop shipped, and email, timesheet, and project tool accounts created\n- Each new hire is **assigned an onboarding buddy** at the same grade or one grade above [onboarding_process.pdf]\n\n### Week One\n- **Day 1:** Orientation, benefits enrollment, and a meeting with the onboarding buddy\n- **Day 2:** Mandatory data security training *(must be completed before accessing any client data)*\n- **Days 3\u20135:** Delivery methodology, timesheet and billable hours rules, and expense policy\n- **New Managers and Partners** also meet with the Managing Partner during week one [onboarding_process.pdf]\n\n### Project Assignment\n- New consultants are assigned to their first project **by the end of week two**\n- Analysts and Consultants join an **existing active project team** and cannot be the sole consultant on a project during their **first 90 days** [onboarding_process.pdf]\n\n### Check-ins & Completion\n- The manager holds formal check-ins at **30, 60, and 90 days**\n- At the 90-day check-in, the manager confirms the consultant is on track for their billable hours target\n- Onboarding is **officially complete** when the 90-day check-in is signed off [onboarding_process.pdf]\n\n[Source: Retrieval Agent | onboarding_process.pdf]"
}
```

## Both (multi-tool)

```json
{
  "question": "How many invoices are currently overdue, and what does our invoicing policy say we should do about overdue invoices?",
  "route": "both",
  "sql_agent_ran": true,
  "retrieval_agent_ran": true,
  "sql_result": {
    "success": true,
    "answer": "There are currently **3 overdue invoices** in the system. However, your question about the invoicing policy falls outside the scope of this data \u2014 the query only retrieves invoice counts, and policy information was not included in the results. You would need to consult your internal policy documentation for guidance on handling overdue invoices.",
    "sources": [
      "SELECT COUNT(*) AS overdue_invoice_count\nFROM invoices\nWHERE status <> 'paid'\nAND due_date < CURRENT_DATE;"
    ],
    "metadata": {
      "tool": "sql_agent",
      "sql_validation": "PASSED",
      "sql": "SELECT COUNT(*) AS overdue_invoice_count\nFROM invoices\nWHERE status <> 'paid'\nAND due_date < CURRENT_DATE;",
      "validation_reason": "Single read-only SELECT",
      "row_count": 1,
      "latency_s": 2.68
    }
  },
  "retrieval_result": {
    "success": true,
    "answer": "Based on the document excerpts provided, I can answer the **policy portion** of your question, but not the count of currently overdue invoices (that would require database records).\n\n## Overdue Invoice Policy\n\nThe invoicing policy outlines a **three-stage escalation process** for overdue invoices: [invoice_and_payment_policy.pdf]\n\n1. **1\u201330 days overdue:** The account manager sends a written reminder to the client's finance contact. [invoice_and_payment_policy.pdf]\n\n2. **31\u201360 days overdue:** The Engagement Manager calls the client sponsor and agrees on a payment date. [invoice_and_payment_policy.pdf]\n\n3. **After 60 days overdue:** The matter is escalated to a Partner, who may place the related project **on hold** until payment is received. Additionally, the firm will **not start new projects** for that client unless a Partner approves an exception in writing. [invoice_and_payment_policy.pdf]\n\n### Disputes\nIf an invoice is disputed, the account manager must log the dispute within **two business days**. Disputed invoices remain overdue until resolved, but the 60-day Partner escalation is **paused** during the investigation. [invoice_and_payment_policy.pdf]\n\n---\nFor the **current count of overdue invoices**, please refer to the billing system or database records, as that information is not available in the provided excerpts.",
    "sources": [
      "invoice_and_payment_policy.pdf"
    ],
    "metadata": {
      "tool": "retrieval_agent",
      "chunk_scores": [
        {
          "doc": "invoice_and_payment_policy.pdf",
          "score": 0.8725
        },
        {
          "doc": "invoice_and_payment_policy.pdf",
          "score": 0.7638
        },
        {
          "doc": "sample-documents/retail-supply-chain-case-study.pdf",
          "score": 0.6635
        },
        {
          "doc": "expense_and_travel_policy.pdf",
          "score": 0.6601
        }
      ],
      "grounded": true,
      "cited_docs": [
        "invoice_and_payment_policy.pdf"
      ],
      "latency_s": 2.96
    }
  },
  "final_answer": "There are currently **3 overdue invoices** in the system [SQL Agent]. According to the invoicing policy, overdue invoices follow a three-stage escalation process: for invoices **1\u201330 days overdue**, the account manager sends a written reminder to the client's finance contact; for **31\u201360 days overdue**, the Engagement Manager calls the client sponsor to agree on a payment date; and **after 60 days**, the matter escalates to a Partner, who may place the related project on hold and block new projects for that client unless a Partner grants a written exception [Retrieval Agent: invoice_and_payment_policy.pdf]. If any of the overdue invoices are disputed, the account manager must log the dispute within two business days, and the 60-day Partner escalation clock is paused during the investigation [Retrieval Agent: invoice_and_payment_policy.pdf]."
}
```
