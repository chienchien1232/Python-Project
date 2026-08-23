# -*- coding: utf-8 -*-
"""Viet lai khoi join 2 dong thanh form can bang chuan cho 4 file."""
import py_compile
import re

FILES = ["src/app/pages/2_teams.py", "src/app/pages/3_players.py",
         "src/app/pages/4_compare.py", "src/app/pages/5_ml_explorer.py"]

pat = re.compile(
    r"= os\.path\.join\(os\.path\.dirname\(os\.path\.dirname\("
    r"os\.path\.dirname\(os\.path\.dirname\(os\.path\.abspath\(__file__\)"
    r"\)\)\)\)\),\s*\"data\", \"processed\", \"analytics\",\s*\"([^\"]+)\"\)")

REPL = (
    "= os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(\n"
    "        os.path.dirname(os.path.abspath(__file__))))),\n"
    "        \"data\", \"processed\", \"analytics\", \"\\1\")"
)

for p in FILES:
    s = open(p, encoding="utf-8").read()
    new, n = pat.subn(REPL, s)
    if n:
        open(p, "w", encoding="utf-8", newline="").write(new)
        print("fixed:", p, f"({n} khoi)")
    else:
        print("khong thay pattern:", p)

for p in FILES:
    py_compile.compile(p, doraise=True)
print("COMPILE ALL OK")
