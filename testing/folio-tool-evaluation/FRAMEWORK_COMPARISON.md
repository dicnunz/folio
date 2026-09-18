# Folio minimal framework comparison

## Scope and counting method

Every prototype implements only these behaviors: assignment name, due date, Low/Medium/High priority, an Add Assignment action, session-only assignment state, a table, and rejection of whitespace-only names. No prototype adds a database, authentication, scheduling, rewards, or email.

The approximate application-code counts below count nonblank runtime source lines. The counts include templates and CSS because the interface requires template and CSS code. The counting method excludes dependency manifests, lockfiles, generated build output, and this comparison report. Formatting affects the figures, so readers should treat the figures as scale indicators rather than productivity scores.

| Candidate | Approx. application code | Required files | Boilerplate/configuration |
|---|---:|---|---|
| Python + Streamlit | 28 lines | `tinyfolio.py`; `streamlit-requirements.txt` | Very low: one application file and no template or routing configuration |
| Python + Flask | 83 lines | `flask_app/app.py`; `flask_app/templates/index.html`; `flask_app/requirements.txt` | Low: application/route setup plus one HTML template |
| Python + Django | 114 lines | `django_app/manage.py`; `django_app/folio/__init__.py`; `settings.py`; `urls.py`; `views.py`; `templates/index.html`; `requirements.txt` | Highest of these prototypes: project settings, URL configuration, middleware, template, and launcher |
| TypeScript + React | 107 lines | `react_app/package.json`; `package-lock.json`; `tsconfig.json`; `index.html`; `src/main.tsx`; `src/App.tsx`; `src/styles.css` | Moderate: package/build configuration, HTML mount point, React bootstrap, component, and CSS |

## Setup and run commands

Tests can run all Python prototypes in one local virtual environment from the repository root:

```sh
python3 -m venv .venv
```

### Python + Streamlit

```sh
.venv/bin/python -m pip install -r streamlit-requirements.txt
.venv/bin/streamlit run tinyfolio.py
```

Direct dependency: Streamlit 1.49.1. Streamlit itself installs a comparatively large transitive dependency set, including Pandas; the Folio source does not import or use Pandas.

### Python + Flask

```sh
.venv/bin/python -m pip install -r flask_app/requirements.txt
.venv/bin/flask --app flask_app/app run
```

Direct dependency: Flask 3.1.2. Flask brings the normal Werkzeug, Jinja, Click, ItsDangerous, Blinker, and MarkupSafe dependencies.

### Python + Django

```sh
.venv/bin/python -m pip install -r django_app/requirements.txt
.venv/bin/python django_app/manage.py runserver
```

Direct dependency: Django 5.2.6. The Django prototype deliberately selects Django's signed-cookie session backend, so the prototype does not need migrations or SQLite.

### TypeScript + React

```sh
cd react_app
npm install
npm run dev
```

Direct runtime dependencies: React 19.1.1 and React DOM 19.1.1. Development dependencies: TypeScript 5.9.2, Vite 7.3.6, and React type declarations. `npm run build` performs the production compile/build check.

## Implementation mechanics

| Candidate | Form input | Session state | Blank-name validation | Table rendering | Framework-specific complications |
|---|---|---|---|---|---|
| Streamlit | Each script rerun reads widget return values; the button controls the add branch | `st.session_state.assignments` stores data for the Streamlit user session | The code calls `name.strip()` and then displays `st.error` when necessary | `st.table` directly renders the list of assignment dictionaries | The whole script reruns after interaction, so developers must keep mutable values in session state. Streamlit's small source file hides a relatively large transitive dependency and runtime stack. |
| Flask | A POST route reads `request.form`; successful posts use redirect-after-post | Flask's signed session cookie stores assignments | Server-side code calls `name.strip()` and passes an error message to the template | Jinja loops over assignments to create HTML rows | Developers write the HTML and styling manually. Cookie sessions need a secret key and have practical size limits, and production deployments must replace the development key. |
| Django | A POST view reads `request.POST`; successful posts redirect | Django signed-cookie sessions store assignments and avoid a database | Server-side code calls `name.strip()` and passes an error message to the template | A Django template loop creates HTML rows | Even this one-page app requires CSRF middleware, settings, URL routing, and project structure. Signed cookies avoid SQLite but retain cookie-size limits. |
| React | Controlled inputs update component state; `onSubmit` handles the form | React `useState` holds data in browser memory for the mounted page | The handler calls `name.trim()` and displays an accessible error message | JSX maps the assignment array into HTML rows | React requires a Node package and build toolchain plus manual state and UI wiring. A page reload intentionally clears state because persistence falls outside this prototype's scope. |

## Functional test results

| Checklist item | Streamlit | Flask | Django | React |
|---|:---:|:---:|:---:|:---:|
| Application launches successfully | Pass | Pass | Pass | Pass |
| Assignment-name input appears | Pass | Pass | Pass | Pass |
| Due-date input appears | Pass | Pass | Pass | Pass |
| Priority selector appears | Pass | Pass | Pass | Pass |
| Add Assignment button appears | Pass | Pass | Pass | Pass |
| User can add a valid assignment | Pass | Pass | Pass | Pass |
| Application displays the correct date and priority | Pass | Pass | Pass | Pass |
| User can add multiple assignments | Pass | Pass | Pass | Pass |
| Earlier assignments remain visible | Pass | Pass | Pass | Pass |
| Application rejects blank assignment names | Pass | Pass | Pass | Pass |
| Normal use does not crash the application | Pass | Pass | Pass | Pass |

Every candidate test used `Design Report / 2026-09-30 / High`, followed by `Second Assignment / 2026-10-05 / Medium`, and then a whitespace-only name. The whitespace-only attempt left the two valid rows unchanged.

Validation evidence:

- All four development servers launched and returned HTTP 200.
- The Streamlit application test harness exercised widget interaction, two rows of retained session state, table values, blank rejection, and exception checks.
- The Flask and Django framework test clients exercised redirects, retained session cookies, rendered values, blank rejection, and HTTP status checks.
- React passed TypeScript compilation and the Vite production build, and a browser then exercised the running interface through the same two-additions-plus-blank sequence.
- `python -m py_compile` passed for all Python source files, `manage.py check` reported no Django issues, and `npm audit` reported zero known vulnerabilities after dependency installation.

## Streamlit inspection result

`tinyfolio.py` required no source correction. The Python compiler accepted `tinyfolio.py`, and the Streamlit test run confirmed the full checklist. The three-space indentation looks unconventional but remains syntactically consistent; the space before `st.selectbox (` causes no problem. The existing `st.session_state` initialization, whitespace validation, list append, date value, and `st.table` usage all follow valid Streamlit patterns for this prototype. The evaluation added only the pinned requirements file for reproducible Streamlit setup.
