# -*- coding: utf-8 -*-
"""Sua thua 1 dong ngoac sau __file__ tren cac line dirname x4."""
import py_compile

FILES = ["src/app/pages/2_teams.py", "src/app/pages/3_players.py",
         "src/app/pages/4_compare.py", "src/app/pages/5_ml_explorer.py"]

BROKEN = "os.path.abspath(__file__))))), "
FIXED = "os.path.abspath(__file__)))), "

for p in FILES:
    s = open(p, encoding="utf-8").read()
    if BROKEN in s:
        s = s.replace(BROKEN, FIXED)
        open(p, "w", encoding="utf-8", newline="").write(s)
        print("fixed:", p)
    else:
        print("khong thay broken pattern:", p)

for p in FILES:
    py_compile.compile(p, doraise=True)
print("COMPILE ALL OK")
