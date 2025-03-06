#!/bin/bash

# Exit immediately if any command exits with a non-zero status
set -e

# Database Configuration
# Sets DB_NAME to POSTGRES_DB if it's provided, otherwise defaults to 'news_db'
DB_NAME="${POSTGRES_DB:-news_db}"
# Sets DB_USER to POSTGRES_USER if it's provided, otherwise defaults to 'postgres'
DB_USER="${POSTGRES_USER:-postgres}"

# Wait for PostgreSQL to start by repeatedly checking its status
until pg_isready -U "$DB_USER"; do
  echo "Waiting for PostgreSQL to start..."
  sleep 2  # Wait for 2 seconds before checking again
done

# Check if the database already exists
# List all databases, format the output, and check if DB_NAME is in the list
if ! psql -U "$DB_USER" -lqt | cut -d\| -f1 | grep -qw "$DB_NAME"; then
  echo "Database '$DB_NAME' does not exist. Creating..."
  # Create the database if it doesn't exist
  psql -U "$DB_USER" -c "CREATE DATABASE $DB_NAME;"
else
  echo "Database '$DB_NAME' already exists."
fi

# Ensure the 'news_articles' table exists in the database
psql -U "$DB_USER" -d "$DB_NAME" <<EOSQL
CREATE TABLE IF NOT EXISTS news_articles (
    id SERIAL PRIMARY KEY,      
    title TEXT NOT NULL,        
    publication_timestamp TIMESTAMP WITH TIME ZONE,  
    weblink TEXT NOT NULL,  
    picture TEXT, 
    tags TEXT[],  
    summary TEXT,
    CONSTRAINT unique_article UNIQUE (title, publication_timestamp)  
);
EOSQL

# Confirmation message
echo "Database and table created successfully."
