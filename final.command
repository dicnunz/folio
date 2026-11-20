#!/bin/zsh
set -eu
cd "${0:A:h}"
export PYTHONDONTWRITEBYTECODE=1
export FOLIO_DATABASE="$PWD/data/academic.sqlite3"
python=.venv/bin/python
[[ -x "$python" ]] || python="$HOME/Desktop/folio/.venv/bin/python"
exec "$python" -m streamlit run app.py --server.address=127.0.0.1 --browser.gatherUsageStats=false
