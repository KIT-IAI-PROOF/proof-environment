#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	CREATE DATABASE proof;
  CREATE DATABASE keycloak;
  GRANT ALL PRIVILEGES ON DATABASE keycloak TO admin;
  GRANT ALL PRIVILEGES ON DATABASE proof TO admin;
EOSQL