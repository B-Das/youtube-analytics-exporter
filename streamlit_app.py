import os

# IMPORTANT: Do not use 'import app' here.
# Python caches modules after first import, so every Streamlit rerun would
# return the cached module without re-executing app.py — causing a blank screen.
# exec() forces app.py to fully re-execute on every rerun, identical to running
# 'streamlit run app.py' directly.
_app_path = os.path.join(os.path.dirname(__file__), "app.py")
with open(_app_path, encoding="utf-8") as _f:
    exec(_f.read(), {"__file__": _app_path, "__name__": "__main__"})
