CREATE
USER  watchdog WITH PASSWORD 'watchdog';

CREATE
DATABASE watchdog
    WITH
    OWNER = watchdog
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;
