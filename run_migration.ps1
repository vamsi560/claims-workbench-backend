# PowerShell script to run PostgreSQL migration for Claims Workbench
# Usage: Open PowerShell, run: ./run_migration.ps1

# Set your migration file path
$migrationFile = "..\supabase\migrations\20260101130839_create_observability_schema.sql"

# Set your database URL
$dbUrl = "postgresql://retool:npg_UWqxdlf1LmS7@ep-round-breeze-af1fyksh.c-2.us-west-2.retooldb.com/retool?sslmode=require"

# Run migration using psql
# Make sure psql is installed and in your PATH
psql "$dbUrl" -f $migrationFile
