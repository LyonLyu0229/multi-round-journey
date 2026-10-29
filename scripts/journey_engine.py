"""Deterministic calendar, path divination and structural planning checks; no writes."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import importlib.metadata
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo, reset_tzpath

sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
# Always use the vendored, pinned IANA database rather than host-dependent rules.
reset_tzpath(())

VERSION = 'journey-v2'
TRIGRAMS = ('乾', '兑', '离', '震', '巽', '坎', '艮', '坤')
BITS = ((1,1,1), (1,1,0), (1,0,1), (1,0,0),
        (0,1,1), (0,1,0), (0,0,1), (0,0,0))
# Rows: upper trigram; columns: lower trigram, in the order above.
KING_WEN = (
    (1,10,13,25,44,6,33,12), (43,58,49,17,28,47,31,45),
    (14,38,30,21,50,64,56,35), (34,54,55,51,32,40,62,16),
    (9,61,37,42,57,59,53,20), (5,60,63,3,48,29,39,8),
    (26,41,22,27,18,4,52,23), (11,19,36,24,46,7,15,2),
)
NAMES = ('乾','坤','屯','蒙','需','讼','师','比','小畜','履','泰','否',
         '同人','大有','谦','豫','随','蛊','临','观','噬嗑','贲','剥','复',
         '无妄','大畜','颐','大过','坎','离','咸','恒','遁','大壮','晋','明夷',
         '家人','睽','蹇','解','损','益','夬','姤','萃','升','困','井','革','鼎',
         '震','艮','渐','归妹','丰','旅','巽','兑','涣','节','中孚','小过','既济','未济')
BRANCHES = '子丑寅卯辰巳午未申酉戌亥'


def integer(value, low, high=None):
    if type(value) is not int or value < low or (high is not None and value > high):
        raise ValueError(f'integer required in range {low}..{high}: {value!r}')
    return value


def encode_path(path):
    if not isinstance(path, list):
        raise ValueError('path must be a list of decision lists')
    p = 0
    for decision in path:
        if not isinstance(decision, list) or not decision:
            raise ValueError('each decision must be a nonempty list')
        codes = [integer(c, 1, 10) for c in decision]
        if len(set(codes)) != len(codes):
            raise ValueError('duplicate option code')
        for code in sorted(codes):
            p = 11 * p + code
        p *= 11
    return p


def describe(upper, lower):
    number = KING_WEN[upper - 1][lower - 1]
    return {'number': number, 'name': NAMES[number - 1],
            'upper': TRIGRAMS[upper - 1], 'lower': TRIGRAMS[lower - 1],
            'lines_bottom_up': list(BITS[lower - 1] + BITS[upper - 1])}


def hexagram(base, hour, path):
    integer(base, 3, 54)
    integer(hour, 1, 12)
    p = encode_path(path)
    n = len(path)
    upper = (base + p - 1) % 8 + 1
    total = base + hour + p + n
    lower = (total - 1) % 8 + 1
    moving = (total - 1) % 6 + 1
    current = describe(upper, lower)
    changed = current['lines_bottom_up'].copy()
    changed[moving - 1] ^= 1
    changed_lower = BITS.index(tuple(changed[:3])) + 1
    changed_upper = BITS.index(tuple(changed[3:])) + 1
    return {'algorithm': VERSION, 'base': base, 'hour': hour,
            'path': [sorted(d) for d in path], 'path_code': str(p), 'step': n,
            'primary': current, 'moving_line': moving,
            'changed': describe(changed_upper, changed_lower)}


def _solar(dt):
    from lunar_python import Solar
    return Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)


def _local_instants(wall, zone, fold):
    found = []
    seen = set()
    for f in (0, 1):
        aware = wall.replace(tzinfo=zone, fold=f)
        utc = aware.astimezone(timezone.utc)
        if utc.astimezone(zone).replace(tzinfo=None) != wall:
            continue
        if utc in seen:
            continue
        seen.add(utc)
        if fold is None or fold == f:
            found.append(aware)
    if not found:
        raise ValueError('nonexistent local time or invalid fold for this wall time')
    return found


def _one_chart(aware):
    # Calendar library treats its solar terms in UTC+8. Match the actual instant.
    bj = aware.astimezone(timezone(timedelta(hours=8))).replace(tzinfo=None)
    standard = aware.replace(tzinfo=None) - aware.dst()
    lunar = _solar(standard).getLunar()
    terms = _solar(bj).getLunar()
    eight = lunar.getEightChar()
    eight.setSect(2)
    pillars = {'year': terms.getYearInGanZhiExact(),
               'month': terms.getMonthInGanZhiExact(),
               'day': eight.getDay(), 'hour': eight.getTime()}
    lunar_year_branch = lunar.getYearInGanZhi()[-1]
    year_number = BRANCHES.index(lunar_year_branch) + 1
    hour = ((standard.hour + 1) // 2) % 12 + 1
    base = year_number + abs(lunar.getMonth()) + lunar.getDay()
    return {'civil_time': aware.isoformat(),
            'utc_time': aware.astimezone(timezone.utc).isoformat(),
            'fold': aware.fold, 'dst_seconds': int(aware.dst().total_seconds()),
            'standard_time': standard.isoformat(), 'pillars': pillars,
            'lunar_standard': {'year': lunar.getYear(), 'month': abs(lunar.getMonth()),
                               'day': lunar.getDay(), 'leap': lunar.getMonth() < 0},
            'birth_numbers': {'year_branch': year_number, 'base': base, 'hour': hour},
            'initial_hexagram': hexagram(base, hour, [])}


def chart(data):
    from lunar_python import Lunar
    if not isinstance(data, dict):
        raise ValueError('birth input must be an object')
    if not data.get('birthplace') or not data.get('timezone'):
        raise ValueError('birthplace and IANA timezone required')
    calendar = data.get('calendar')
    if calendar not in ('solar', 'lunar'):
        raise ValueError('calendar must be solar or lunar')
    year = integer(data['year'], 1, 9999)
    month = integer(data['month'], 1, 12)
    day = integer(data['day'], 1, 31)
    leap = data.get('leap', False)
    if type(leap) is not bool or (calendar == 'solar' and leap):
        raise ValueError('leap must be boolean, only for lunar input')
    if calendar == 'lunar':
        try:
            value = Lunar.fromYmd(year, -month if leap else month, day)
        except Exception as exc:
            raise ValueError(f'invalid lunar date: {exc}') from exc
        solar = value.getSolar()
        date = datetime(solar.getYear(), solar.getMonth(), solar.getDay())
        back = _solar(date).getLunar()
        if (back.getYear(), back.getMonth(), back.getDay()) != (year, -month if leap else month, day):
            raise ValueError('invalid lunar date')
    else:
        date = datetime(year, month, day)
    wall = datetime.fromisoformat(date.strftime('%Y-%m-%d') + 'T' + data['time'])
    if wall.tzinfo is not None:
        raise ValueError('time must be a local clock time, not an offset timestamp')
    end = wall
    if data.get('time_end'):
        end_date = data.get('end_date', date.strftime('%Y-%m-%d'))
        end = datetime.fromisoformat(end_date + 'T' + data['time_end'])
    if not timedelta(0) <= end - wall <= timedelta(hours=48):
        raise ValueError('time range must be forward, at most 48 hours; use end_date across midnight')
    if end.tzinfo is not None:
        raise ValueError('time_end must be a local clock time')
    fold = data.get('fold')
    if fold is not None:
        integer(fold, 0, 1)
    zone = ZoneInfo(data['timezone'])
    candidates = {}
    samples = {wall, end}
    t = wall
    while t <= end:
        samples.add(t)
        t += timedelta(minutes=1)
    # Include exact pillar hour boundaries even when the starting second is nonzero.
    t = wall.replace(minute=0, second=0, microsecond=0)
    while t <= end:
        if wall <= t:
            samples.add(t)
        t += timedelta(hours=1)
    # Include solar-term instants and the preceding second, which minute sampling
    # could otherwise miss when a term and a clock boundary are close together.
    for term in _solar(wall).getLunar().getJieQiTable().values():
        term_bj = datetime.fromisoformat(term.toYmdHms()).replace(tzinfo=timezone(timedelta(hours=8)))
        local_term = term_bj.astimezone(zone).replace(tzinfo=None)
        for instant in (local_term - timedelta(seconds=1), local_term):
            if wall <= instant <= end:
                samples.add(instant)
    for sample in sorted(samples):
        for aware in _local_instants(sample, zone, fold):
            result = _one_chart(aware)
            # Include offset/fold in the key so a historical repeated hour is not hidden.
            key = (tuple(result['pillars'].values()), result['birth_numbers']['base'],
                   result['birth_numbers']['hour'], aware.utcoffset(), aware.fold)
            if key not in candidates:
                result['range_start'] = aware.isoformat()
                result['range_end'] = aware.isoformat()
                candidates[key] = result
            else:
                candidates[key]['range_end'] = aware.isoformat()
    return {'algorithm': VERSION, 'calendar_library': importlib.metadata.version('lunar-python'),
            'tzdata_version': importlib.metadata.version('tzdata'),
            'policy': 'civil timezone; remove DST for day/hour; instant-based jieqi; midnight day; no true solar correction',
            'candidates': list(candidates.values())}


def audit(ledger):
    """Structural guard, not a proof of causal sufficiency or reality."""
    errors = []
    if not isinstance(ledger, dict):
        raise ValueError('ledger must be an object')
    def index(items, label):
        result = {}
        for item in items:
            key = item.get('id')
            if not key or key in result:
                errors.append(f'{label}: missing or duplicate id {key}')
            else:
                result[key] = item
        return result
    goal = ledger.get('goal', {})
    criteria = index(goal.get('criteria', []), 'criterion')
    if not goal.get('id') or not criteria:
        errors.append('goal id and nonempty criteria required')
    nodes = index(ledger.get('nodes', []), 'node')
    active = ledger.get('active_path', [])
    if not active or len(set(active)) != len(active):
        errors.append('nonempty unique active_path required')
    path = []
    previous = None
    birth_numbers = None
    for node_id in active:
        node = nodes.get(node_id, {})
        if not node or node.get('parent') != previous:
            errors.append(f'{node_id}: broken active ancestry')
        codes = node.get('options', [])
        selected = node.get('selected', [])
        try:
            encode_path([codes])
            encode_path([selected])
            if not set(selected).issubset(codes):
                raise ValueError('unknown selected option')
            if len(selected) > 1 and sorted(selected) not in node.get('compatible_combinations', []):
                raise ValueError('combination not declared compatible')
            path.append(selected)
            h = node.get('hexagram', {})
            pair = (h.get('base'), h.get('hour'))
            if birth_numbers is not None and birth_numbers != pair:
                errors.append(f'{node_id}: birth numbers changed inside path')
            birth_numbers = pair
            expected = hexagram(h.get('base'), h.get('hour'), path)
            if h != expected:
                errors.append(f'{node_id}: hexagram does not replay')
        except (ValueError, TypeError, KeyError) as exc:
            errors.append(f'{node_id}: {exc}')
        if not node.get('state_before') or not node.get('state_after') or node['state_before'] == node['state_after']:
            errors.append(f'{node_id}: missing state transition')
        if previous in nodes and node.get('state_before') != nodes[previous].get('state_after'):
            errors.append(f'{node_id}: state does not continue parent')
        if not node.get('interpretation') or not isinstance(node.get('gaps'), list):
            errors.append(f'{node_id}: missing interpretation/gap view')
        if node.get('gaps') and not node.get('next_options'):
            errors.append(f'{node_id}: open gaps without next options')
        previous = node_id
    if active and nodes.get(active[-1], {}).get('gaps') != []:
        errors.append('terminal node still has open gaps')
    actions = index(ledger.get('actions', []), 'action')
    covered = set()
    for aid, action in actions.items():
        if action.get('source_node') not in active:
            errors.append(f'{aid}: action source not in selected path')
        elif aid not in nodes[action['source_node']].get('action_ids', []):
            errors.append(f'{aid}: not registered in source decision')
        for field in ('task', 'deliverable', 'acceptance', 'resources'):
            if not action.get(field):
                errors.append(f'{aid}: missing {field}')
        covers = action.get('covers', [])
        if not covers or not set(covers).issubset(criteria):
            errors.append(f'{aid}: unknown or empty coverage')
        covered.update(covers)
    for cid in criteria:
        if cid not in covered:
            errors.append(f'{cid}: no selected action covers condition')
    for node_id in active:
        for aid in nodes.get(node_id, {}).get('action_ids', []):
            if aid not in actions or actions[aid].get('source_node') != node_id:
                errors.append(f'{node_id}: declared action {aid} missing or has wrong source')
    visiting, visited = set(), set()
    def visit(aid):
        if aid in visiting:
            errors.append(f'{aid}: cyclic dependency')
            return
        if aid in visited:
            return
        visiting.add(aid)
        deps = actions[aid].get('depends_on', [])
        for dep in deps:
            if dep not in actions:
                errors.append(f'{aid}: unknown dependency {dep}')
            else:
                visit(dep)
        visiting.remove(aid)
        visited.add(aid)
    for aid in actions:
        visit(aid)
    checks = ledger.get('external_checks', [])
    for cid, criterion in criteria.items():
        if criterion.get('kind') not in ('controlled', 'resource', 'external'):
            errors.append(f'{cid}: invalid condition kind')
        if criterion.get('kind') == 'external' and not any(
            c.get('condition_id') == cid and all(c.get(k) for k in ('metric','checkpoint','fallback'))
            for c in checks):
            errors.append(f'{cid}: external validation/fallback missing')
    for key in ('unresolved_decisions', 'resource_conflicts'):
        if key not in ledger or ledger[key] != []:
            errors.append(f'{key}: missing or unresolved')
    return {'planning_status': 'in_progress' if errors else 'closed',
            'actual_goal_status': 'unverified', 'errors': errors,
            'semantic_review_required': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('chart', 'audit'):
        p = sub.add_parser(name)
        src = p.add_mutually_exclusive_group(required=True)
        src.add_argument('--json')
        src.add_argument('--input', help='UTF-8 JSON file, or - for stdin')
    p = sub.add_parser('hex')
    p.add_argument('--base', required=True, type=int)
    p.add_argument('--hour', required=True, type=int)
    p.add_argument('--path', default='[]')
    args = parser.parse_args()
    try:
        if args.command == 'hex':
            result = hexagram(args.base, args.hour, json.loads(args.path))
        else:
            raw = args.json if args.json is not None else (
                sys.stdin.read() if args.input == '-' else Path(args.input).read_text(encoding='utf-8-sig'))
            data = json.loads(raw)
            result = chart(data) if args.command == 'chart' else audit(data)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, TypeError, KeyError, ImportError, OverflowError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
