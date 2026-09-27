import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('measure_aim_journey', Path(__file__).resolve().parents[1] / 'scripts/measure_aim_journey.py')
journey = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(journey)


def event(second, kind, **data):
    return {'at': f'2026-09-27T12:00:{second:02d}Z', 'kind': kind, **data}


class JourneyMeasurementTests(unittest.TestCase):
    def test_latency_includes_interruption_and_resume_delay(self):
        result = journey.report([event(0, 'observation_started'), event(1, 'authorized'), event(5, 'interruption'), event(9, 'operator_intervention'), event(12, 'product_observed', file='app.py')])
        self.assertEqual(result['firstProductCodeSeconds'], 11)
        self.assertEqual(len(result['interventions']), 1)
        self.assertEqual(len(result['injectedInterruptions']), 1)
        self.assertIsNone(result['classification']['administrativeRepairs']['count'])

    def test_missing_or_late_observer_and_existing_code_are_unknown(self):
        for events in (
            [event(1, 'authorized')],
            [event(1, 'authorized'), event(2, 'observation_started'), event(3, 'product_observed')],
            [event(0, 'observation_started'), event(0, 'product_baseline'), event(1, 'authorized'), event(3, 'product_observed')],
            [event(0, 'observation_started'), event(1, 'authorized'), event(2, 'observation_gap'), event(3, 'product_observed')],
        ):
            with self.subTest(events=events):
                self.assertIsNone(journey.report(events)['firstProductCodeSeconds'])

    def test_complete_review_required_for_zero_and_evidence_required_for_findings(self):
        events = [event(1, 'authorized')]
        review = {'completeTranscriptReviewed': True, 'transcriptSha256': 'a' * 64, 'unnecessaryQuestions': [], 'administrativeRepairs': [{'reason': 'migration'}]}
        result = journey.report(events, review)
        self.assertEqual(result['classification']['unnecessaryQuestions']['count'], 0)
        self.assertIsNone(result['classification']['administrativeRepairs']['count'])
        review['administrativeRepairs'][0]['evidence'] = 'turn 1 item 3'
        self.assertEqual(journey.report(events, review)['classification']['administrativeRepairs']['count'], 1)

    def test_birthtime_is_independent_and_must_be_inside_authorized_window(self):
        events = [event(1, 'authorized'), event(2, 'observation_gap'), event(10, 'product_observed', createdAt='2026-09-27T12:00:05Z')]
        result = journey.report(events)
        self.assertEqual(result['firstProductCodeSeconds'], 4)
        self.assertEqual(result['latencySource'], 'filesystem_birthtime')
        for created in ('2026-09-27T12:00:00Z', '2026-09-27T12:00:11Z'):
            events[-1]['createdAt'] = created
            self.assertIsNone(journey.report(events)['firstProductCodeSeconds'])

    def test_ambiguous_authorization_and_naive_time_rejected(self):
        for events in ([], [event(1, 'authorized'), event(2, 'authorized')], [{'at': '2026-09-27T12:00:00', 'kind': 'authorized'}]):
            with self.assertRaises(ValueError): journey.report(events)

    def test_observer_does_not_modify_project_and_records_baseline(self):
        import json
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); repo = root / 'repo'; repo.mkdir()
            code = repo / 'app.py'; code.write_text('print(42)\n')
            output = root / 'events.jsonl'
            journey.observe(repo, ['app.py'], output, .02, .01)
            events = [json.loads(line) for line in output.read_text().splitlines()]
            self.assertEqual([e['kind'] for e in events], ['observation_started', 'product_baseline', 'observation_ended'])
            self.assertEqual(code.read_text(), 'print(42)\n')
            self.assertEqual(list(repo.iterdir()), [code])
            for files, target in ((['../outside.py'], output), (['app.py'], repo/'events.jsonl')):
                with self.assertRaises(ValueError): journey.observe(repo, files, target, .01, .01)

    def test_out_of_order_evidence_sorted_and_pre_authorization_intervention_excluded(self):
        result = journey.report([event(10, 'product_observed'), event(0, 'observation_started'), event(0, 'operator_intervention'), event(1, 'authorized')])
        self.assertEqual(result['firstProductCodeSeconds'], 9)
        self.assertEqual(result['interventions'], [])


if __name__ == '__main__': unittest.main()
