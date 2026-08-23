# -*- coding: utf-8 -*-
"""Fix import os/sys + helpers path trong tat ca cac trang Streamlit."""
import os

PAGES_DIR = os.path.join("src", "app", "pages")
TARGETS = ["1_matches.py", "2_teams.py", "3_players.py",
           "4_compare.py", "5_ml_explorer.py"]

HEADER_FIX = '''import os
import sys

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
'''

for fn in TARGETS:
    path = os.path.join(PAGES_DIR, fn)
    s = open(path, encoding="utf-8").read()

    # bo dong sys.path cu (dung ../ hoac dirname thieu)
    old_line = None
    for cand in ('sys.path.insert(0, "..")',
                 "sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))"):
        if cand in s:
            old_line = cand
            break
    # xoa import os/sys cu de chen header moi khong trung lap
    s = s.replace("import os\nimport sys\n\n", "")
    s = s.replace("import sys\n\nimport pandas as pd", "\nimport pandas as pd")
    s = s.replace("import sys\n\nimport plotly.express as px",
                  "\nimport plotly.express as px")
    s = s.replace("\nimport sys\n\nimport pandas as pd",
                  "\nimport pandas as pd")

    # chen header chuan sau dong encoding/docstring dau tien
    marker_end_doc = s.find('"""', s.find('"""') + 3) + 3
    s = s[:marker_end_doc] + "\n\n" + HEADER_FIX + s[marker_end_doc:]

    open(path, "w", encoding="utf-8", newline="").write(s)
    print("fixed:", fn)

# verify compile
import py_compile
for fn in TARGETS:
    py_compile.compile(os.path.join(PAGES_DIR, fn), doraise=True)
print("COMPILE ALL OK")
