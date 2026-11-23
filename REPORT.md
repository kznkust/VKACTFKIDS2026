# Отчёт о реорганизации VKACTFKIDS2026

Образец: https://github.com/userbusser/StudentCTF-2024 — структура `categories/<категория>/<префикс>-<сложность>-<имя>/{give,solution/writeup.md}`.

## Общие изменения

- Распакованы все 25 архивов `*-main.zip`; после распаковки исходные архивы удалены из корня.
- Таски разложены по `categories/{crypto,forensics,misc,osint,pwn,reverse,web}`.
- Имена приведены к виду `<cat>-<easy|medium|hard>-<имя>` (сокращения `_e_/_m_/_h_` раскрыты, разделители унифицированы).
- `solve/` → `solution/`; райтапы `WRITEUP.md` / `README.md` → `solution/writeup.md`.
- Шапка каждого `writeup.md` приведена к единому формату: `# Название` + таблица «Событие | Название | Категория | Сложность» с событием `VKACTF Kids 2026` (раньше было вперемешку: `ctf_rev_school`, `VKAKIDS 2026`, `vkactfkids2026`, `revers` и т.п.). Если старый заголовок был описанием техники (pwn/rev), он сохранён жирной строкой под таблицей.
- Удалены: папки `source/` (crypto, с `private.json` и генераторами) и `deploy/src/` (pwn, rev), все README (шаблоны, заметки организатора, `player_README.md`), а также мусор: `.github/`, `__pycache__/`, `.gitignore`.
- Корневой `README.md` переписан в стиле образца: ссылки ведут на `solution/writeup.md`, отсортировано по сложности.

## Требует внимания

- Сложность `kodoburg`, `place`, `reversi` уточнена вручную: `cry-easy-kodoburg`, `osint-hard-place`, `rev-medium-reversi`.
- **`web-hard-blackout`**: добавлен в `categories/web/web-hard-blackout` и в README. ⚠️ Содержимое архива побайтово совпадает с `web-hard-undertow` (код и райтап — от Undertow); в шапке райтапа название заменено на «Blackout». Если появится правильная версия — нужно заменить.
- Таски только с райтапом, без `give/`: `for-hard-two_channels`, `for-medium-dnstagram`, `osint-hard-place`, `web-easy-secret_print`, `web-medium-second_decode`, `web-hard-double_exposure`, `cry-easy-kodoburg`.
- Вложенные архивы внутри `give/` (`give.rar`, `pocket_orchestra.zip`, `copy.zip` и др.) — это раздача игрокам, не распаковывались.
- У crypto-райтапов нет раздела «Описание» (сразу «Решение») — содержимое не трогал.

## Повторная проверка (после правок сложности)

- README пересобран: ссылка на `rev-easy-reversi` была битой → теперь `rev-medium-reversi`, порядок по сложности обновлён.
- Скриптом проверено для всех 26 тасков: имя папки `<cat>-<easy|medium|hard>-<имя>`, префикс соответствует категории, есть `solution/writeup.md`, сложность/категория/название в шапке совпадают с папкой, не осталось `src/`, `source/`, `solve/`, README, `.github/`, `__pycache__/`; все ссылки README рабочие и все таски в нём есть — **OK**.
- `give/flag.txt` в pwn-тасках — фейковые флаги, настоящие только в `deploy/`.
- Исправлены относительные ссылки в райтапах после переноса `solve/` → `solution/`: `./give/…` → `../give/…`, `./solve/solve.py` → `./solve.py` (`rev-easy-carbon_copy`, `rev-hard-palimpsest`, `rev-medium-after_the_bell`).
- Битые ссылки, которых не было уже в исходных архивах: `requirements.txt` в `cry-medium-clockwork` и `cry-medium-quadratic_atlas`, `give/bookplate.txt` в `rev-hard-palimpsest`.

## Удаление deploy/ и dev/

По запросу удалены папки `deploy/` и `dev/` во всех тасках (вместе с серверными флагами, исходниками и Docker-файлами). В тасках остались только `give/` и `solution/`, как в образце. Удалено:

- `categories/misc/misc-hard-nullchoir/deploy/`
- `categories/misc/misc-hard-voidcustoms/deploy/`
- `categories/pwn/pwn-easy-buffer_overflow/deploy/`
- `categories/pwn/pwn-easy-buffer_overflow/dev/`
- `categories/pwn/pwn-hard-pocket_orchestra/deploy/`
- `categories/pwn/pwn-hard-thermal_archive/deploy/`
- `categories/reverse/rev-easy-carbon_copy/deploy/`
- `categories/reverse/rev-hard-palimpsest/deploy/`
- `categories/reverse/rev-medium-after_the_bell/deploy/`
- `categories/reverse/rev-medium-boardvm/dev/`
- `categories/web/web-hard-blackout/deploy/`
- `categories/web/web-hard-palimpsest/deploy/`
- `categories/web/web-hard-undertow/deploy/`

## Изменения по таскам

### web-hard-blackout
- распакован в `categories/web/web-hard-blackout`
- удалено: `.github/`, `README.md`
- шапка writeup.md приведена к единому формату (название «Blackout»)
- архив `web-hard-blackout-main.zip` удалён из корня после распаковки


### cry-medium-rational_notary
- переименовано: `cry_m_rational_notary` → `cry-medium-rational_notary`
- `solution/README.md` → `solution/writeup.md`
- удалено: `source/`
- шапка writeup.md приведена к единому формату

### cry-medium-carry_baggage
- переименовано: `cry_m_carry_baggage` → `cry-medium-carry_baggage`
- `solution/README.md` → `solution/writeup.md`
- удалено: `source/`
- шапка writeup.md приведена к единому формату

### cry-medium-noisy_choir
- переименовано: `cry_m_noisy_choir` → `cry-medium-noisy_choir`
- `solution/README.md` → `solution/writeup.md`
- удалено: `source/`
- шапка writeup.md приведена к единому формату

### cry-medium-quadratic_atlas
- переименовано: `cry_m_quadratic_atlas` → `cry-medium-quadratic_atlas`
- `solution/README.md` → `solution/writeup.md`
- удалено: `source/`
- шапка writeup.md приведена к единому формату

### cry-medium-mirrorarchive
- переименовано: `cry_m_mirrorarchive` → `cry-medium-mirrorarchive`
- `solution/README.md` → `solution/writeup.md`
- удалено: `source/`
- шапка writeup.md приведена к единому формату

### cry-medium-clockwork
- переименовано: `cry_m_clockwork` → `cry-medium-clockwork`
- `solution/README.md` → `solution/writeup.md`
- удалено: `source/`
- шапка writeup.md приведена к единому формату

### cry-easy-kodoburg
- переименовано: `crypto-kodoburg` → `cry-easy-kodoburg`
- `solution/WRITEUP.md` → `solution/writeup.md`
- удалено: `README.md`
- шапка writeup.md приведена к единому формату

### for-hard-two_channels
- переименовано: `for_h_two_channels` → `for-hard-two_channels`
- папка `solve/` → `solution/`
- `solution/WRITEUP.md` → `solution/writeup.md`
- шапка writeup.md приведена к единому формату

### for-medium-dnstagram
- переименовано: `for_m_dnstagram` → `for-medium-dnstagram`
- папка `solve/` → `solution/`
- `solution/WRITEUP.md` → `solution/writeup.md`
- шапка writeup.md приведена к единому формату

### misc-hard-voidcustoms
- удалено: `.github/`
- удалено: `README.md`
- шапка writeup.md приведена к единому формату

### misc-hard-nullchoir
- удалено: `.github/`
- удалено: `README.md`
- шапка writeup.md приведена к единому формату

### osint-hard-place
- переименовано: `osint-place` → `osint-hard-place`
- `solution/WRITEUP.md` → `solution/writeup.md`
- шапка writeup.md приведена к единому формату

### pwn-hard-thermal_archive
- переименовано: `pwn_h_thermal_archive` → `pwn-hard-thermal_archive`
- папка `solve/` → `solution/`
- удалено: `deploy/src/`
- шапка writeup.md приведена к единому формату

### pwn-hard-pocket_orchestra
- переименовано: `pwn_h_pocket_orchestra` → `pwn-hard-pocket_orchestra`
- папка `solve/` → `solution/`
- удалено: `deploy/src/`
- шапка writeup.md приведена к единому формату

### pwn-easy-buffer_overflow
- переименовано: `pwn-easy-buffer-overflow` → `pwn-easy-buffer_overflow`
- удалено: `.gitignore`
- удалено: `README.md`
- удалено: `dev/player_README.md`
- удалено: `deploy/README.md`
- шапка writeup.md приведена к единому формату

### rev-easy-carbon_copy
- переименовано: `rev_e_carbon_copy` → `rev-easy-carbon_copy`
- папка `solve/` → `solution/`
- удалено: `deploy/src/`
- удалено: `deploy/README.md`
- шапка writeup.md приведена к единому формату

### rev-medium-after_the_bell
- переименовано: `rev_m_after_the_bell` → `rev-medium-after_the_bell`
- папка `solve/` → `solution/`
- удалено: `deploy/src/`
- удалено: `deploy/README.md`
- шапка writeup.md приведена к единому формату

### rev-hard-palimpsest
- переименовано: `rev_h_palimpsest` → `rev-hard-palimpsest`
- папка `solve/` → `solution/`
- удалено: `deploy/src/`
- удалено: `deploy/README.md`
- шапка writeup.md приведена к единому формату

### rev-medium-reversi
- переименовано: `revers-reversi` → `rev-medium-reversi`
- `solution/WRITEUP.md` → `solution/writeup.md`
- шапка writeup.md приведена к единому формату

### rev-medium-boardvm
- переименовано: `reverse-medium-boardvm` → `rev-medium-boardvm`
- удалено: `README.md`
- удалено: `dev/__pycache__/`
- удалено: `dev/player_README.md`
- удалено: `dev/README.md`
- удалено: `dev/build/README.md`
- удалено: `solution/__pycache__/`
- шапка writeup.md приведена к единому формату

### web-easy-secret_print
- переименовано: `web_e_secret_print` → `web-easy-secret_print`
- папка `solve/` → `solution/`
- `solution/WRITEUP.md` → `solution/writeup.md`
- шапка writeup.md приведена к единому формату

### web-medium-second_decode
- переименовано: `web_m_second_decode` → `web-medium-second_decode`
- папка `solve/` → `solution/`
- `solution/WRITEUP.md` → `solution/writeup.md`
- шапка writeup.md приведена к единому формату

### web-hard-double_exposure
- переименовано: `web_h_double_exposure` → `web-hard-double_exposure`
- папка `solve/` → `solution/`
- `solution/WRITEUP.md` → `solution/writeup.md`
- шапка writeup.md приведена к единому формату

### web-hard-palimpsest
- удалено: `.github/`
- удалено: `README.md`
- шапка writeup.md приведена к единому формату

### web-hard-undertow
- удалено: `.github/`
- удалено: `README.md`
- шапка writeup.md приведена к единому формату

