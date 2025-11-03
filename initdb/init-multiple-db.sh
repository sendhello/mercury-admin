#!/bin/sh
set -e

# Список баз
DBS="postgres"

for db in $DBS; do
  echo "Creating database: $db"
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE "$db";
EOSQL

owner="${db}_owner"      # владелец/миграции
app="${db}_app"          # пользователь приложения

# Ожидаем пароли в переменных окружения:
#   AUTH_OWNER_PASSWORD, AUTH_APP_PASSWORD,
#   ORDERS_OWNER_PASSWORD, ORDERS_APP_PASSWORD,
#   ROUTE_PLANNING_OWNER_PASSWORD, ROUTE_PLANNING_APP_PASSWORD
upper_db=$(echo "$db" | tr '[:lower:]' '[:upper:]')
owner_pw_var="${upper_db}_OWNER_PASSWORD"
app_pw_var="${upper_db}_APP_PASSWORD"
# косвенное чтение переменных
eval owner_pw=\${$owner_pw_var:-}
eval app_pw=\${$app_pw_var:-}

if [ -z "$owner_pw" ] || [ -z "$app_pw" ]; then
  echo "ERROR: set $owner_pw_var and $app_pw_var env vars for passwords" >&2
  exit 1
fi

echo "Creating roles for $db: $owner (owner), $app (app)"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
  -- создаём роли, если их ещё нет
  DO \$\$
  BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$owner') THEN
      CREATE ROLE "$owner" LOGIN PASSWORD '$owner_pw';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$app') THEN
      CREATE ROLE "$app" LOGIN PASSWORD '$app_pw';
    END IF;
  END
  \$\$;

  -- передаём владение базой роли владельца
  ALTER DATABASE "$db" OWNER TO "$owner";
EOSQL

# Назначаем права внутри конкретной БД
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$db" <<-EOSQL
  -- база: убираем PUBLIC, разрешаем connect нужным ролям
  REVOKE ALL ON DATABASE "$db" FROM PUBLIC;
  GRANT CONNECT ON DATABASE "$db" TO "$owner","$app";

  -- схема public: только владелец может CREATE
  REVOKE CREATE ON SCHEMA public FROM PUBLIC;
  GRANT USAGE, CREATE ON SCHEMA public TO "$owner";
  GRANT USAGE ON SCHEMA public TO "$app";

  -- существующие объекты
  GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO "$app";
  GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO "$app";

  -- дефолтные права для будущих объектов, создаваемых владельцем
  ALTER DEFAULT PRIVILEGES FOR ROLE "$owner" IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "$app";
  ALTER DEFAULT PRIVILEGES FOR ROLE "$owner" IN SCHEMA public
    GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO "$app";
EOSQL
done
