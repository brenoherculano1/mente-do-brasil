-- PUBLIC privileges are inherited by anon/authenticated even after direct revocation.
REVOKE USAGE ON SCHEMA public FROM PUBLIC;
REVOKE EXECUTE ON ALL ROUTINES IN SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO mente_do_brasil_api;
GRANT EXECUTE ON ALL ROUTINES IN SCHEMA public TO mente_do_brasil_api;
