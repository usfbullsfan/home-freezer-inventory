# PostgreSQL Setup and Migration Guide

This guide covers setting up PostgreSQL for the Freezer Inventory Tracker and migrating from SQLite.

## Table of Contents

- [Why PostgreSQL?](#why-postgresql)
- [Quick Start](#quick-start)
- [Local PostgreSQL Setup](#local-postgresql-setup)
- [Cloud PostgreSQL Setup](#cloud-postgresql-setup)
- [Migration from SQLite](#migration-from-sqlite)
- [Troubleshooting](#troubleshooting)

---

## Why PostgreSQL?

The application defaults to SQLite, which works great for single-user and development scenarios. Consider PostgreSQL when you need:

- **Multi-user support**: Better concurrent access handling
- **Cloud deployment**: Most cloud platforms offer managed PostgreSQL (AWS RDS, GCP Cloud SQL, Azure Database)
- **Scalability**: Better performance with larger datasets
- **Production reliability**: ACID compliance, better backup/restore options
- **Advanced features**: Full-text search, JSON support, replication

**SQLite is still recommended for:**
- Single-user deployments
- Development and testing
- Simple home use cases
- Low-traffic applications

---

## Quick Start

### Using PostgreSQL Instead of SQLite

1. **Install PostgreSQL adapter**:
   ```bash
   cd backend
   pip install -r requirements.txt  # Includes psycopg2-binary
   ```

2. **Set DATABASE_URL**:
   ```bash
   # In .env file or environment
   DATABASE_URL=postgresql://username:password@host:port/database
   ```

3. **Start the application**:
   ```bash
   python app.py
   ```

The application will automatically detect `DATABASE_URL` and use PostgreSQL instead of SQLite.

---

## Local PostgreSQL Setup

### macOS

#### Install PostgreSQL

```bash
# Using Homebrew
brew install postgresql@15
brew services start postgresql@15
```

#### Create Database

```bash
# Create user and database
psql postgres

# In psql:
CREATE USER freezer_user WITH PASSWORD 'your_secure_password';
CREATE DATABASE freezer_inventory OWNER freezer_user;
GRANT ALL PRIVILEGES ON DATABASE freezer_inventory TO freezer_user;
\q
```

#### Configure Application

```bash
# In backend/.env
DATABASE_URL=postgresql://freezer_user:your_secure_password@localhost:5432/freezer_inventory
```

### Linux (Ubuntu/Debian)

#### Install PostgreSQL

```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### Create Database

```bash
# Switch to postgres user
sudo -u postgres psql

# In psql:
CREATE USER freezer_user WITH PASSWORD 'your_secure_password';
CREATE DATABASE freezer_inventory OWNER freezer_user;
GRANT ALL PRIVILEGES ON DATABASE freezer_inventory TO freezer_user;
\q
```

#### Configure Application

```bash
# In backend/.env
DATABASE_URL=postgresql://freezer_user:your_secure_password@localhost:5432/freezer_inventory
```

### Windows

#### Install PostgreSQL

1. Download installer from [postgresql.org](https://www.postgresql.org/download/windows/)
2. Run installer and follow wizard
3. Remember the password you set for the postgres user
4. Default port is 5432

#### Create Database

```bash
# Open PowerShell or CMD
# Navigate to PostgreSQL bin directory
cd "C:\Program Files\PostgreSQL\15\bin"

# Connect to PostgreSQL
psql -U postgres

# In psql:
CREATE USER freezer_user WITH PASSWORD 'your_secure_password';
CREATE DATABASE freezer_inventory OWNER freezer_user;
GRANT ALL PRIVILEGES ON DATABASE freezer_inventory TO freezer_user;
\q
```

#### Configure Application

```bash
# In backend/.env
DATABASE_URL=postgresql://freezer_user:your_secure_password@localhost:5432/freezer_inventory
```

### Docker

Quick setup using Docker:

```bash
# Start PostgreSQL container
docker run -d \
  --name freezer-postgres \
  -e POSTGRES_USER=freezer_user \
  -e POSTGRES_PASSWORD=your_secure_password \
  -e POSTGRES_DB=freezer_inventory \
  -p 5432:5432 \
  -v freezer_pgdata:/var/lib/postgresql/data \
  postgres:15-alpine

# Configure application
# DATABASE_URL=postgresql://freezer_user:your_secure_password@localhost:5432/freezer_inventory
```

---

## Cloud PostgreSQL Setup

### AWS RDS

#### 1. Create RDS Instance

```bash
# Via AWS Console:
# 1. RDS → Create database
# 2. Engine: PostgreSQL
# 3. Template: Free tier (or Production)
# 4. DB instance: db.t3.micro (or larger)
# 5. Master username: freezer_admin
# 6. Master password: [set secure password]
# 7. DB name: freezer_inventory
# 8. Public access: Yes (if accessing from outside VPC)
# 9. Create database
```

#### 2. Configure Security Group

```bash
# Allow PostgreSQL access (port 5432)
# Add inbound rule:
# Type: PostgreSQL
# Port: 5432
# Source: Your IP or 0.0.0.0/0 (less secure)
```

#### 3. Get Connection String

```bash
# From RDS console, get endpoint
# Format: your-instance.xxxxx.region.rds.amazonaws.com

# Set in .env:
DATABASE_URL=postgresql://freezer_admin:your_password@your-instance.xxxxx.us-east-1.rds.amazonaws.com:5432/freezer_inventory
```

### GCP Cloud SQL

#### 1. Create Cloud SQL Instance

```bash
# Via GCP Console:
# 1. SQL → Create Instance → PostgreSQL
# 2. Instance ID: freezer-inventory-db
# 3. Password: [set secure password]
# 4. Region: [choose nearest]
# 5. Database version: PostgreSQL 15
# 6. Machine type: Shared core (or larger)
# 7. Create instance
```

#### 2. Create Database

```bash
# In Cloud SQL console:
# 1. Select instance
# 2. Databases → Create database
# 3. Name: freezer_inventory
# 4. Create
```

#### 3. Configure Connection

**Option A: Public IP (Simple)**

```bash
# Enable public IP in Cloud SQL instance
# Add authorized network (your IP)

# Connection string:
DATABASE_URL=postgresql://postgres:your_password@PUBLIC_IP:5432/freezer_inventory
```

**Option B: Cloud SQL Proxy (Recommended)**

```bash
# Install Cloud SQL Proxy
wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
chmod +x cloud_sql_proxy

# Run proxy (replace with your instance connection name)
./cloud_sql_proxy -instances=PROJECT:REGION:INSTANCE=tcp:5432 &

# Connection string (connects via proxy):
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/freezer_inventory
```

### Azure Database for PostgreSQL

#### 1. Create PostgreSQL Server

```bash
# Via Azure Portal:
# 1. Create a resource → Azure Database for PostgreSQL
# 2. Deployment option: Single server
# 3. Server name: freezer-inventory
# 4. Admin username: freezer_admin
# 5. Password: [set secure password]
# 6. Version: 15
# 7. Compute + storage: Basic (or higher)
# 8. Create
```

#### 2. Configure Firewall

```bash
# Add firewall rule to allow connections
# Settings → Connection security
# Add your IP or enable "Allow access to Azure services"
```

#### 3. Connection String

```bash
DATABASE_URL=postgresql://freezer_admin@freezer-inventory:your_password@freezer-inventory.postgres.database.azure.com:5432/freezer_inventory?sslmode=require
```

### Heroku

```bash
# Heroku automatically provisions PostgreSQL
# Add PostgreSQL addon
heroku addons:create heroku-postgresql:mini

# Get DATABASE_URL (automatically set)
heroku config:get DATABASE_URL

# No manual configuration needed!
```

---

## Migration from SQLite

### Prerequisites

- Existing SQLite database with data
- PostgreSQL instance set up and running
- DATABASE_URL configured

### Migration Steps

#### 1. Backup Your SQLite Database

```bash
# Create backup
cd backend
cp instance/freezer_inventory.db instance/freezer_inventory.db.backup
```

#### 2. Set Environment Variables

```bash
# In backend/.env or environment
DATABASE_URL=postgresql://username:password@host:port/database

# Optional: specify custom SQLite path
SQLITE_DB_PATH=instance/freezer_inventory.db
```

#### 3. Run Migration Script

```bash
cd backend
python migrate_sqlite_to_postgres.py
```

The script will:
- Connect to both databases
- Check if PostgreSQL is empty (warn if not)
- Create PostgreSQL schema
- Copy all data (users, categories, items, settings)
- Update PostgreSQL sequences
- Verify migration

#### 4. Verify Migration

```bash
# Start application with PostgreSQL
python app.py

# Check that all data is present
# - Users can log in
# - Categories exist
# - Items are displayed
```

#### 5. Update Production Configuration

```bash
# Update .env or environment variables to use DATABASE_URL
# Restart application
```

### Migration Output Example

```
============================================================
SQLite to PostgreSQL Migration
============================================================

Step 1: Connecting to databases...
✓ Connected to SQLite database: /path/to/freezer_inventory.db
✓ Connected to PostgreSQL database

Step 2: Checking PostgreSQL database...

Step 3: Creating PostgreSQL schema...
✓ PostgreSQL tables created

Step 4: Migrating data...
  Found 3 users
  Found 18 categories
  Found 245 items
  Found 5 settings
  ✓ Migrated 3 users
  ✓ Migrated 18 categories
  ✓ Migrated 245 items
  ✓ Migrated 5 settings
  ✓ Updated PostgreSQL sequences

============================================================
Migration completed successfully!
============================================================

Migrated:
  • 3 users
  • 18 categories
  • 245 items
  • 5 settings

Your application is now ready to use PostgreSQL.
```

---

## Troubleshooting

### Connection Refused

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check port is correct (default: 5432)
psql -h localhost -p 5432 -U freezer_user -d freezer_inventory

# Check firewall allows port 5432
sudo ufw allow 5432/tcp
```

### Authentication Failed

```bash
# Verify credentials
psql -U freezer_user -d freezer_inventory

# Reset password if needed
sudo -u postgres psql
ALTER USER freezer_user WITH PASSWORD 'new_password';
```

### "psycopg2" Module Not Found

```bash
# Install PostgreSQL adapter
cd backend
pip install -r requirements.txt

# Or install directly
pip install psycopg2-binary
```

### SSL Required (Cloud Databases)

```bash
# Add sslmode to connection string
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

### Migration Fails - Existing Tables

```bash
# The migration script will prompt before dropping tables
# To manually clean PostgreSQL:
psql -U freezer_user -d freezer_inventory

# Drop all tables
DROP TABLE IF EXISTS items, categories, users, settings CASCADE;
\q

# Re-run migration
python migrate_sqlite_to_postgres.py
```

### Slow Performance

```bash
# Create indexes (already done in models.py, but verify)
psql -U freezer_user -d freezer_inventory

# Check indexes
\di

# Vacuum and analyze
VACUUM ANALYZE;
```

### Connection Pool Exhausted

```bash
# Increase max connections in PostgreSQL
# Edit postgresql.conf:
max_connections = 100

# Or use connection pooling (PgBouncer)
```

---

## Performance Tuning

### PostgreSQL Configuration

For production, tune these settings in `postgresql.conf`:

```conf
# Memory settings (adjust based on available RAM)
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
work_mem = 4MB

# Connection settings
max_connections = 100

# Write-ahead log
wal_buffers = 16MB
checkpoint_completion_target = 0.9

# Query planner
random_page_cost = 1.1  # Lower for SSD
```

### Application-Level

```python
# In backend/.env, configure connection pooling
SQLALCHEMY_POOL_SIZE=10
SQLALCHEMY_POOL_RECYCLE=3600
SQLALCHEMY_MAX_OVERFLOW=20
```

---

## Backup and Restore

### Backup

```bash
# Full database backup
pg_dump -U freezer_user -h localhost freezer_inventory > backup.sql

# Compressed backup
pg_dump -U freezer_user -h localhost -Fc freezer_inventory > backup.dump

# Automated daily backups
# Add to crontab:
0 2 * * * pg_dump -U freezer_user freezer_inventory > ~/backups/freezer_$(date +\%Y\%m\%d).sql
```

### Restore

```bash
# From SQL file
psql -U freezer_user -h localhost freezer_inventory < backup.sql

# From compressed dump
pg_restore -U freezer_user -h localhost -d freezer_inventory backup.dump

# Cloud storage backup (AWS S3 example)
pg_dump -U freezer_user freezer_inventory | gzip | aws s3 cp - s3://my-bucket/backup.sql.gz
```

---

## Switching Back to SQLite

If you need to switch back to SQLite:

1. **Remove or comment out DATABASE_URL**:
   ```bash
   # In .env
   # DATABASE_URL=postgresql://...
   ```

2. **Restart application**:
   ```bash
   python app.py
   ```

The application will automatically use SQLite.

To migrate data back from PostgreSQL to SQLite, you can use the migration script in reverse or export/import manually.

---

## Best Practices

1. **Use Environment Variables**: Never hardcode credentials in code
2. **Use SSL**: Always use SSL for production databases (`sslmode=require`)
3. **Regular Backups**: Automate daily backups
4. **Monitor Connections**: Use connection pooling for high-traffic scenarios
5. **Update Regularly**: Keep PostgreSQL updated with security patches
6. **Use Read Replicas**: For high-read scenarios, set up read replicas
7. **Database User Permissions**: Use least-privilege principle

---

## Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy PostgreSQL Dialect](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html)
- [AWS RDS PostgreSQL](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html)
- [GCP Cloud SQL](https://cloud.google.com/sql/docs/postgres)
- [Azure Database for PostgreSQL](https://docs.microsoft.com/en-us/azure/postgresql/)

---

## Support

For PostgreSQL-specific issues, please open a GitHub issue with the `database` and `postgresql` labels.
