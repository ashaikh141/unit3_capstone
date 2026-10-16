from validator import validate_sql


def test_case1_valid_select_is_allowed():
    r = validate_sql("SELECT name FROM clients WHERE region = 'North'")
    assert r["valid"] is True
    assert r["status"] == "PASSED"


def test_case2_destructive_statements_are_blocked():
    for sql in ["DROP TABLE clients",
                "DELETE FROM invoices",
                "UPDATE projects SET status = 'closed'",
                "INSERT INTO clients (name) VALUES ('x')"]:
        r = validate_sql(sql)
        assert r["valid"] is False, sql
        assert r["status"] == "BLOCKED", sql


def test_case3_column_containing_blocked_word_is_allowed():
    r = validate_sql("SELECT id, deleted_at, updated_by, created_date FROM projects")
    assert r["valid"] is True


def test_case4_stacked_query_with_blocked_keyword_is_blocked():
    r = validate_sql("SELECT * FROM clients; DROP TABLE clients")
    assert r["valid"] is False


def test_case5_stacked_query_of_two_selects_is_blocked():
    assert validate_sql("SELECT * FROM clients")["valid"] is True
    assert validate_sql("SELECT * FROM invoices")["valid"] is True
    r = validate_sql("SELECT * FROM clients; SELECT * FROM invoices")
    assert r["valid"] is False
    assert "stacked" in r["reason"].lower()


def test_single_trailing_semicolon_is_allowed():
    assert validate_sql("SELECT COUNT(*) FROM projects;")["valid"] is True


def test_lowercase_destructive_is_blocked():
    assert validate_sql("drop table clients")["valid"] is False


def test_blocked_word_inside_string_literal_is_allowed():
    assert validate_sql("SELECT * FROM projects WHERE name = 'do not DROP this'")["valid"] is True


def test_semicolon_hidden_by_string_trick_is_blocked():
    assert validate_sql("SELECT 'a--b'; DROP TABLE clients")["valid"] is False


def test_cte_with_delete_is_blocked():
    assert validate_sql("WITH x AS (DELETE FROM invoices RETURNING *) SELECT * FROM x")["valid"] is False


def test_select_into_is_blocked():
    assert validate_sql("SELECT * INTO backup_clients FROM clients")["valid"] is False


def test_empty_query_is_blocked():
    assert validate_sql("   ")["valid"] is False