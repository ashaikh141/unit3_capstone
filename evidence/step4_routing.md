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
      "latency_s": 1.56
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
    "answer": "## Consultant Onboarding Process\n\nBased on the onboarding documentation, here is a summary of the full process:\n\n### Before Day One\n- People Operations sends a **welcome pack one week before** the start date [onboarding_process.pdf]\n- IT ships a laptop and creates email, timesheet, and project tool accounts [onboarding_process.pdf]\n- Each new hire is assigned an **onboarding buddy** at the same grade or one grade above [onboarding_process.pdf]\n\n### Week One\n- **Day 1:** Orientation, benefits enrollment, and a meeting with the onboarding buddy [onboarding_process.pdf]\n- **Day 2:** Mandatory data security training, which must be completed before accessing any client data [onboarding_process.pdf]\n- **Days 3\u20135:** Delivery methodology, timesheet and billable hours rules, and expense policy [onboarding_process.pdf]\n- New **Managers and Partners** also meet the Managing Partner during week one [onboarding_process.pdf]\n\n### Project Assignment\n- New consultants are assigned to their first project **by the end of week two** [onboarding_process.pdf]\n- Analysts and Consultants must join an existing team and cannot be the **sole consultant on a project during their first 90 days** [onboarding_process.pdf]\n\n### Check-ins & Completion\n- Formal check-ins are held at **30, 60, and 90 days** by the new hire's manager [onboarding_process.pdf]\n- Onboarding is officially **complete when the 90-day check-in is signed off** [onboarding_process.pdf]",
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
      "latency_s": 9.67
    }
  },
  "final_answer": "## Consultant Onboarding Process\n\nBased on the onboarding documentation, here is a summary of the full process:\n\n### Before Day One\n- People Operations sends a **welcome pack one week before** the start date [onboarding_process.pdf]\n- IT ships a laptop and creates email, timesheet, and project tool accounts [onboarding_process.pdf]\n- Each new hire is assigned an **onboarding buddy** at the same grade or one grade above [onboarding_process.pdf]\n\n### Week One\n- **Day 1:** Orientation, benefits enrollment, and a meeting with the onboarding buddy [onboarding_process.pdf]\n- **Day 2:** Mandatory data security training, which must be completed before accessing any client data [onboarding_process.pdf]\n- **Days 3\u20135:** Delivery methodology, timesheet and billable hours rules, and expense policy [onboarding_process.pdf]\n- New **Managers and Partners** also meet the Managing Partner during week one [onboarding_process.pdf]\n\n### Project Assignment\n- New consultants are assigned to their first project **by the end of week two** [onboarding_process.pdf]\n- Analysts and Consultants must join an existing team and cannot be the **sole consultant on a project during their first 90 days** [onboarding_process.pdf]\n\n### Check-ins & Completion\n- Formal check-ins are held at **30, 60, and 90 days** by the new hire's manager [onboarding_process.pdf]\n- Onboarding is officially **complete when the 90-day check-in is signed off** [onboarding_process.pdf]\n\n[Source: Retrieval Agent | onboarding_process.pdf]"
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
    "answer": "There are currently **3 overdue invoices** in the system. As for what your invoicing policy says about handling overdue invoices, that information is not available in the query results provided \u2014 you would need to consult your internal policy documentation directly for guidance on next steps.",
    "sources": [
      "SELECT COUNT(*) AS overdue_invoice_count\nFROM invoices\nWHERE status <> 'paid'\nAND due_date < CURRENT_DATE;"
    ],
    "metadata": {
      "tool": "sql_agent",
      "sql_validation": "PASSED",
      "sql": "SELECT COUNT(*) AS overdue_invoice_count\nFROM invoices\nWHERE status <> 'paid'\nAND due_date < CURRENT_DATE;",
      "validation_reason": "Single read-only SELECT",
      "row_count": 1,
      "latency_s": 2.3
    }
  },
  "retrieval_result": {
    "success": true,
    "answer": "Regarding the **number of currently overdue invoices**, I cannot answer that \u2014 the document excerpts provided contain only policy text and do not include any live invoice data. NOT_FOUND for the current count.\n\nHowever, here is what the **invoicing policy states about overdue invoices**:\n\n---\n\n### Overdue Escalation Process [invoice_and_payment_policy.pdf]\n\nOverdue invoices are handled in **three escalating stages**:\n\n1. **1\u201330 days overdue:** The **Account Manager** sends a written reminder to the client's finance contact. [invoice_and_payment_policy.pdf]\n\n2. **31\u201360 days overdue:** The **Engagement Manager** calls the client sponsor and agrees on a payment date. [invoice_and_payment_policy.pdf]\n\n3. **After 60 days overdue:** The matter is escalated to a **Partner**, who may place the related project **on hold** until payment is received. [invoice_and_payment_policy.pdf]\n\n### Additional Rules [invoice_and_payment_policy.pdf]\n\n- The firm **will not start new projects** for a client with any invoice more than 60 days overdue, unless a Partner approves an exception **in writing**. [invoice_and_payment_policy.pdf]\n- If an invoice is **disputed**, the account manager logs it within two business days, and the 60-day Partner escalation is **paused** during investigation, though the invoice remains overdue. [invoice_and_payment_policy.pdf]",
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
      "latency_s": 3.4
    }
  },
  "final_answer": "There are currently **3 overdue invoices** in the system [SQL Agent]. According to the invoicing policy, overdue invoices are handled through a three-stage escalation process: for invoices **1\u201330 days overdue**, the Account Manager sends a written reminder to the client's finance contact; for **31\u201360 days overdue**, the Engagement Manager calls the client sponsor to agree on a payment date; and **after 60 days**, the matter escalates to a Partner, who may place the related project on hold until payment is received [Retrieval Agent: invoice_and_payment_policy.pdf]. Additionally, the firm will not start new projects for a client with any invoice more than 60 days overdue unless a Partner approves an exception in writing, and disputed invoices pause the 60-day escalation clock while still remaining classified as overdue [Retrieval Agent: invoice_and_payment_policy.pdf]."
}
```
