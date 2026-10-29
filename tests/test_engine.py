import copy
from datetime import datetime, timedelta
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import journey_engine as j


def birth(**changes):
    data = dict(calendar='solar', year=1992, month=4, day=1, time='16:30',
                birthplace='calendar fixture', timezone='Asia/Shanghai')
    data.update(changes)
    return data


def one(**changes):
    return j.chart(birth(**changes))['candidates'][0]


class CalendarTests(unittest.TestCase):
    def test_known_date_and_four_pillars(self):
        result = one()
        self.assertEqual(result['pillars'], dict(year='壬申', month='癸卯', day='丁未', hour='戊申'))
        self.assertEqual(result['lunar_standard'], dict(year=1992, month=2, day=29, leap=False))
        self.assertEqual(result['birth_numbers'], dict(year_branch=9, base=40, hour=9))

    def test_solar_lunar_roundtrip(self):
        self.assertEqual(one()['pillars'], one(calendar='lunar', month=2, day=29)['pillars'])

    def test_leap_month(self):
        result = one(calendar='lunar', year=2023, month=2, day=1, leap=True)
        self.assertEqual(result['civil_time'][:10], '2023-03-22')
        self.assertTrue(result['lunar_standard']['leap'])
        self.assertEqual(result['birth_numbers']['base'], 4+2+1)

    def test_invalid_leap_month(self):
        with self.assertRaises(ValueError):
            one(calendar='lunar', year=2023, month=3, day=1, leap=True)

    def test_lichun_boundary(self):
        before = one(year=2024, month=2, day=4, time='16:27:06')
        after = one(year=2024, month=2, day=4, time='16:27:07')
        self.assertEqual(before['pillars']['year'], '癸卯')
        self.assertEqual(after['pillars']['year'], '甲辰')
        self.assertNotEqual(before['pillars']['month'], after['pillars']['month'])

    def test_lunar_year_distinct_from_jieqi_year(self):
        result = one(year=2024, month=2, day=5)
        self.assertEqual(result['pillars']['year'], '甲辰')
        self.assertEqual(result['birth_numbers']['year_branch'], 4)

    def test_jingzhe_boundary(self):
        self.assertEqual(one(year=2024, month=3, day=5, time='10:22:44')['pillars']['month'], '丙寅')
        self.assertEqual(one(year=2024, month=3, day=5, time='10:22:45')['pillars']['month'], '丁卯')

    def test_midnight_and_late_zi(self):
        late = one(time='23:30')
        next_day = one(day=2, time='00:30')
        self.assertEqual(late['pillars']['day'], '丁未')
        self.assertEqual(next_day['pillars']['day'], '戊申')
        self.assertEqual(late['pillars']['hour'], '壬子')
        self.assertEqual(next_day['pillars']['hour'], '壬子')

    def test_historical_china_dst(self):
        result = one(year=1990, month=7, day=1, time='16:30')
        self.assertEqual(result['dst_seconds'], 3600)
        self.assertTrue(result['standard_time'].endswith('15:30:00'))

    def test_dst_nonexistent_time(self):
        with self.assertRaises(ValueError):
            one(year=2024, month=3, day=10, time='02:30', timezone='America/New_York')

    def test_dst_repeated_time_candidates(self):
        result = j.chart(birth(year=2024, month=11, day=3, time='01:30', timezone='America/New_York'))
        self.assertEqual(len(result['candidates']), 2)
        self.assertNotEqual(result['candidates'][0]['utc_time'], result['candidates'][1]['utc_time'])

    def test_foreign_timezone_term_instant(self):
        # 2024 LiChun at 08:27:07 UTC, or 03:27:07 EST.
        before = one(year=2024, month=2, day=4, time='03:27:06', timezone='America/New_York')
        after = one(year=2024, month=2, day=4, time='03:27:07', timezone='America/New_York')
        self.assertEqual(before['pillars']['year'], '癸卯')
        self.assertEqual(after['pillars']['year'], '甲辰')

    def test_uncertain_hour_candidates(self):
        result = j.chart(birth(time='16:59', time_end='17:01'))
        self.assertEqual({c['birth_numbers']['hour'] for c in result['candidates']}, {9,10})

    def test_uncertain_midnight_candidates(self):
        result = j.chart(birth(time='23:59', time_end='00:01', end_date='1992-04-02'))
        self.assertEqual({c['pillars']['day'] for c in result['candidates']}, {'丁未','戊申'})

    def test_uncertain_term_candidates(self):
        result = j.chart(birth(year=2024, month=2, day=4, time='16:27:06', time_end='16:27:08'))
        self.assertEqual({c['pillars']['year'] for c in result['candidates']}, {'癸卯','甲辰'})

    def test_invalid_date_and_range(self):
        for changes in (dict(month=2, day=31), dict(time='16:30+08:00'),
                        dict(time='23:59', time_end='00:01'), dict(time='25:00')):
            with self.assertRaises((ValueError, TypeError)):
                one(**changes)


class HexagramTests(unittest.TestCase):
    def test_birth_initial(self):
        result = j.hexagram(40,9,[])
        self.assertEqual(result['primary']['name'], '泰')
        self.assertEqual(result['moving_line'], 1)
        self.assertEqual(result['changed']['name'], '升')

    def test_all_64_numbers_and_names(self):
        values = [j.describe(u,l) for u in range(1,9) for l in range(1,9)]
        self.assertEqual({v['number'] for v in values}, set(range(1,65)))
        # Independent structural anchors, including reversed upper/lower examples.
        for u,l,number,name in ((1,7,33,'遁'), (3,7,56,'旅'), (7,1,26,'大畜'),
                               (6,3,63,'既济'), (3,6,64,'未济'), (8,5,46,'升')):
            self.assertEqual(j.describe(u,l)['number'], number)
            self.assertEqual(j.describe(u,l)['name'], name)

    def test_every_changed_line(self):
        for base in range(3,55):
            for hour in range(1,13):
                result = j.hexagram(base,hour,[])
                a,b = result['primary']['lines_bottom_up'],result['changed']['lines_bottom_up']
                self.assertEqual([i+1 for i in range(6) if a[i]!=b[i]], [result['moving_line']])

    def test_combination_normalization_and_sequential_distinction(self):
        self.assertEqual(j.hexagram(40,9,[[5,4]]),j.hexagram(40,9,[[4,5]]))
        self.assertNotEqual(j.encode_path([[4,5]]),j.encode_path([[4],[5]]))

    def test_replay_and_large_integer(self):
        path = [[10]]*100
        a,b = j.hexagram(40,9,path),j.hexagram(40,9,path)
        self.assertEqual(a,b)
        self.assertIsInstance(a['path_code'],str)
        self.assertGreater(int(a['path_code']),2**53)

    def test_invalid_paths(self):
        for path in ([[]],[[True]],[[0]],[[11]],[[1,1]],[1],None):
            with self.assertRaises(ValueError):
                j.hexagram(40,9,path)


def ledger():
    selected = [4,5]
    h = j.hexagram(40,9,[selected])
    return {'goal':{'id':'joint-goal','criteria':[
        {'id':'visual','kind':'controlled'}, {'id':'sales','kind':'external'},
        {'id':'travel-funds','kind':'resource'}]},
        'nodes':[{'id':'R1','parent':None,'options':[1,2,3,4,5],
                  'selected':selected,'compatible_combinations':[[4,5]],'hexagram':h,
                  'action_ids':['sample'],
                  'state_before':{'decided':[]},'state_after':{'decided':['visual','devlog']},
                  'interpretation':'卦象提示积累，选择有限样板并核算同步记录时间。',
                  'gaps':['sales','travel-funds'],'next_options':[1,2,3,4,5]}],
        'active_path':['R1'],
        'actions':[{'id':'sample','source_node':'R1','covers':['visual'],'depends_on':[],
                    'task':'制作样板并记录','deliverable':'展示视频','acceptance':'可展示',
                    'resources':{'hours':80}}],
        'external_checks':[], 'unresolved_decisions':[], 'resource_conflicts':[]}


class JourneyTests(unittest.TestCase):
    def test_d_plus_e_is_not_joint_goal_completion(self):
        result = j.audit(ledger())
        self.assertEqual(result['planning_status'],'in_progress')
        self.assertTrue(any('sales' in e for e in result['errors']))
        self.assertTrue(any('travel-funds' in e for e in result['errors']))

    def test_ten_decisions_keep_divination_and_gaps(self):
        data=ledger()
        path=[[4,5]]
        for n in range(2,11):
            prior=data['nodes'][-1]
            path.append([n%5+1])
            node={'id':f'R{n}','parent':prior['id'],'options':[1,2,3,4,5],
                  'selected':path[-1],'hexagram':j.hexagram(40,9,path),
                  'state_before':prior['state_after'], 'state_after':{'decision_count':n},
                  'interpretation':f'本轮{n}依动爻调整准备顺序，销售验证尚未安排。',
                  'gaps':['sales','travel-funds'],'next_options':[1,2,3,4,5]}
            data['nodes'].append(node)
            data['active_path'].append(node['id'])
        result=j.audit(data)
        self.assertEqual(result['planning_status'],'in_progress')
        self.assertFalse(any('replay' in e or 'transition' in e or 'parent' in e for e in result['errors']))
        damaged=copy.deepcopy(data)
        damaged['nodes'][6].pop('hexagram')
        self.assertTrue(any('R7:' in e for e in j.audit(damaged)['errors']))

    def closed_fixture(self):
        data=ledger()
        data['nodes'][0]['gaps']=[]
        for cid in ('sales','travel-funds'):
            # This synthetic structurally-closed fixture declares the actions in
            # the decision record too; causal sufficiency still needs human review.
            data['nodes'][0]['action_ids'].append(cid)
            data['actions'].append(dict(id=cid,source_node='R1',covers=[cid],depends_on=['sample'],
                                        task='chosen task',deliverable='specified output',
                                        acceptance='specified check',resources={'hours':10}))
        data['external_checks']=[dict(condition_id='sales',metric='paid units',checkpoint='review date',fallback='selected fallback route')]
        return data

    def test_structural_completion_is_not_real_success(self):
        result=j.audit(self.closed_fixture())
        self.assertEqual(result['errors'],[])
        self.assertEqual(result['planning_status'],'closed')
        self.assertEqual(result['actual_goal_status'],'unverified')
        self.assertTrue(result['semantic_review_required'])

    def test_reject_unselected_action_and_cycles(self):
        data=self.closed_fixture()
        data['actions'][0]['source_node']='unselected'
        data['actions'][0]['depends_on']=['sales']
        result=j.audit(data)
        self.assertTrue(any('source' in e for e in result['errors']))
        self.assertTrue(any('cyclic' in e for e in result['errors']))

    def test_reject_action_invented_at_terminal(self):
        data=self.closed_fixture()
        data['nodes'][0]['action_ids'].remove('sales')
        self.assertTrue(any('not registered' in e for e in j.audit(data)['errors']))

    def test_revised_branch_replay_and_archive(self):
        data=ledger()
        old=copy.deepcopy(data['nodes'][0])
        data['nodes'][0]['id']='R1-new'
        data['nodes'][0]['selected']=[1]
        data['nodes'][0]['hexagram']=j.hexagram(40,9,[[1]])
        data['nodes'].append(old)
        data['active_path']=['R1-new']
        self.assertTrue(any('source' in e for e in j.audit(data)['errors']))
        self.assertEqual(old['hexagram'],j.hexagram(40,9,[[4,5]]))
        self.assertNotEqual(old['hexagram']['path_code'],data['nodes'][0]['hexagram']['path_code'])


if __name__=='__main__':
    unittest.main()
