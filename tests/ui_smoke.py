"""Run with: python tests/ui_smoke.py (requires project dependencies)."""
from pathlib import Path
import sys

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src' / 'app'))

from media_ui import flag_url, player_photo_url, player_portrait


def verify(app, label):
    assert not app.exception, f'{label}: {[e.message for e in app.exception]}'
    assert not app.error, f'{label}: {[e.value for e in app.error]}'
    print(f'PASS {label}', flush=True)


assert flag_url('Mexico').endswith('/MEX')
assert player_photo_url('Kylian Mbappe')
assert 'data:image/svg+xml' in player_portrait('Future Test Player')
print('PASS official media index', flush=True)


for page in [ROOT / 'src/app/app.py', *sorted((ROOT / 'src/app/pages').glob('*.py'))]:
    app = AppTest.from_file(str(page), default_timeout=120).run()
    verify(app, page.stem)
    # Exercise real data-dependent filter paths, not just static rendering.
    for i in range(len(app.selectbox)):
        if len(app.selectbox[i].options) > 1:
            app.selectbox[i].select_index(1).run()
            verify(app, f'{page.stem} selectbox {i}')
    if page.stem == '6_best_xi':
        for i in range(len(app.radio[0].options)):
            app.radio[0].set_value(app.radio[0].options[i]).run()
            verify(app, f'Best XI mode {i}')


detail_page = ROOT / 'src/app/pages/7_match_detail.py'
valid_detail = AppTest.from_file(str(detail_page), default_timeout=120)
valid_detail.query_params['match_id'] = '1'
valid_detail.run()
verify(valid_detail, 'match detail valid id')

missing_detail = AppTest.from_file(str(detail_page), default_timeout=120)
missing_detail.query_params['match_id'] = '9999'
missing_detail.run()
verify(missing_detail, 'match detail unknown id')

matches_page = ROOT / 'src/app/pages/1_matches.py'
upcoming_matches = AppTest.from_file(str(matches_page), default_timeout=120).run()
status_options = list(upcoming_matches.selectbox[2].options)
if 'Upcoming' in status_options:
    upcoming_matches.selectbox[2].set_value('Upcoming').run()
else:
    upcoming_matches.selectbox[2].select_index(len(status_options) - 1).run()
verify(upcoming_matches, 'matches status filter')

searched_matches = AppTest.from_file(str(matches_page), default_timeout=120).run()
searched_matches.text_input[0].input('Mexico').run()
verify(searched_matches, 'matches text search')

players_page = ROOT / 'src/app/pages/3_players.py'
compare_workspace = AppTest.from_file(str(players_page), default_timeout=120)
compare_workspace.query_params['view'] = 'compare'
compare_workspace.run()
assert len(compare_workspace.tabs) == 2, 'merged Players comparison tabs are missing'
assert len(compare_workspace.selectbox) >= 4, 'merged comparison selectors are missing'
verify(compare_workspace, 'players merged compare workspace')

ml_page = ROOT / 'src/app/pages/5_ml_explorer.py'
ml_workspace = AppTest.from_file(str(ml_page), default_timeout=120).run()
assert len(ml_workspace.tabs) == 3, 'ML Analytics tools are missing'
assert len(ml_workspace.button) >= 1, 'ML cluster actions are missing'
ml_workspace.button[0].click().run()
verify(ml_workspace, 'ML cluster dialog action')
