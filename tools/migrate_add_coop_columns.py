#!/usr/bin/env python3
"""
Migration helper: add missing columns `hp_map` and `cooldowns` to coop_session table
This is a minimal, idempotent script intended for the development SQLite DB located in
`instance/cybersecurity_simulator.db`.

It will:
 - inspect the `coop_session` table columns
 - add `hp_map` and/or `cooldowns` as TEXT columns if they're not present

Run from the project root: python tools/migrate_add_coop_columns.py
"""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'cybersecurity_simulator.db')

if not os.path.exists(DB_PATH):
    print(f"Database file not found at {DB_PATH}. Ensure you're running this from the project root and the DB exists.")
    raise SystemExit(1)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

def get_columns(table_name):
    cur.execute("PRAGMA table_info(%s)" % table_name)
    return [row[1] for row in cur.fetchall()]

print(f"Inspecting table 'coop_session' in DB: {DB_PATH}")
cols = get_columns('coop_session')
print("Existing columns:", cols)

to_add = []
if 'hp_map' not in cols:
    to_add.append(('hp_map', 'TEXT'))
if 'cooldowns' not in cols:
    to_add.append(('cooldowns', 'TEXT'))

if not to_add:
    print("No columns to add. Migration not required.")
    conn.close()
    raise SystemExit(0)

for col_name, col_type in to_add:
    sql = f"ALTER TABLE coop_session ADD COLUMN {col_name} {col_type};"
    print(f"Adding column: {col_name} {col_type}")
    try:
        cur.execute(sql)
        conn.commit()
        print(f"✓ Added column {col_name}")
    except Exception as e:
        print(f"Failed to add column {col_name}: {e}")

print("Migration finished. Final column list:")
print(get_columns('coop_session'))
conn.close()
