import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import adapters

print("=== Step 1: Foundation check ===\n")
print("RDS (one-line query per table):")
for table in ["clients", "projects", "consultants", "invoices"]:
    n = adapters.run_select(f"SELECT COUNT(*) AS row_count FROM {table}")[0]["row_count"]
    print(f"  SELECT COUNT(*) FROM {table:<12} -> {n:>5} rows   {'PASS' if n > 0 else 'FAIL'}")

print("\nOpenSearch:")
n = adapters.count_documents()
print(f"  document count in index '{adapters.INDEX}' -> {n}   {'PASS' if n > 0 else 'FAIL'}")

print("\nOpenSearch index fields (set VECTOR_FIELD / TEXT_FIELD / SOURCE_FIELD in .env to match):")
for name, typ in adapters.get_index_fields().items():
    print(f"  {name}: {typ}")

print("\nDatabase schema (use this to write good test questions):")
print(adapters.get_schema_text())