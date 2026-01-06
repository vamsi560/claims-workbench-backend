import os
import psycopg2

# Migration SQL file path
MIGRATION_FILE = os.path.join(os.path.dirname(__file__), '..', 'supabase', 'migrations', '20260101130839_create_observability_schema.sql')

# Database URL from environment or hardcoded
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://retool:npg_UWqxdlf1LmS7@ep-round-breeze-af1fyksh.c-2.us-west-2.retooldb.com/retool?sslmode=require')

# Read migration SQL
with open(MIGRATION_FILE, 'r') as f:
    migration_sql = f.read()

# Connect and run migration
try:
    print('Connecting to database...')
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    with conn.cursor() as cur:
        print('Running migration...')
        cur.execute(migration_sql)
    print('Migration completed successfully.')
except Exception as e:
    print(f'Error running migration: {e}')
finally:
    if 'conn' in locals():
        conn.close()
