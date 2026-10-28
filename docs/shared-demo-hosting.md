# Shared demo hosting

Run `streamlit run cloud_app.py` for the password-gated hosted app. `app.py` retains the local SQLite workflow.

Configure these server-only Streamlit secrets: `FOLIO_DEMO_PASSWORD`, `FOLIO_SUPABASE_URL`, `FOLIO_SUPABASE_KEY`, and `FOLIO_STORAGE_TOKEN`. Never commit their values. Missing configuration blocks access. The password input is masked; its value is cleared after submission.

Everyone with the demo password uses one shared workspace. Each operation loads the latest SQLite snapshot from the Supabase `folio_demo_state` row. Saves replace that row only when its version still matches, preventing concurrent writes from silently overwriting one another. A network error does not count as a confirmed save. Existing validation, relationships, transaction rules, and schema migrations are retained.

Supabase is authoritative; Streamlit session state and server files are not the saved database. Temporary SQLite files are used only to create/migrate the schema and are removed afterward. Server restarts and new browser sessions reload remote data.

The table uses RLS. Its publishable API key alone cannot read or change the data; the server additionally supplies a random storage token checked against a SHA-256 digest in the policies. This token is separate from the short demo password. Keep both in Streamlit secrets.

App branch: `codex/course-site-app`. Course-site link: `main`, `docs/index.html`. Public address: https://dicnunz-folio.streamlit.app/ .
