"""Run the shipped helper in an isolated consumer and recover saved answers."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InteractionPackageTests(unittest.TestCase):
    def test_shipped_cli_recovery_uses_existing_evidence_without_runtime_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / 'package'
            shutil.copytree(ROOT / 'skills/agile-iteration-method', package)
            consumer = root / 'consumer'
            evidence = consumer / '.aim/analysis'
            evidence.mkdir(parents=True)
            ledger = consumer / '.aim/product-backlog.json'
            ledger.write_text('{"sentinel":"existing runtime"}\n')
            original = ledger.read_bytes()
            helper = package / 'scripts/aim_interaction.py'

            def cli(command, payload, expected=0):
                before = sorted(p.relative_to(consumer) for p in consumer.rglob('*'))
                result = subprocess.run(
                    [sys.executable, '-I', '-S', str(helper), command],
                    input=json.dumps(payload), text=True, capture_output=True, cwd=consumer,
                )
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                self.assertEqual(before, sorted(p.relative_to(consumer) for p in consumer.rglob('*')))
                self.assertEqual(ledger.read_bytes(), original)
                return json.loads(result.stdout)

            def question(identity, dependencies=()):
                return dict(id=identity, revision=1, scope='Checkout behavior',
                            prompt='When may checkout proceed?', kind='choice', decisionType='product',
                            dependsOn=list(dependencies), recommendedOptionId='verified', options=[
                                dict(id='immediate', label='Immediately', meaning='Proceed without verification'),
                                dict(id='verified', label='After verification', meaning='Require verification first')])

            batch = dict(id='checkout', revision=1, scope='Checkout',
                         questions=[question('verify'), question('notify', ['verify'])])
            capabilities = dict(structured=True, maxQuestions=3, freeText=True, asynchronous=True)
            presented = cli('prepare', dict(batch=batch, capabilities=capabilities))
            self.assertEqual([q['id'] for q in presented['questions']], ['verify'])
            self.assertEqual(presented['questions'][0]['options'][0]['id'], 'verified')
            response = dict(event='submit', submitted=True, batchId=presented['batchId'],
                            batchRevision=presented['batchRevision'], presentationDigest=presented['digest'],
                            source='Explicit fixture response; provenance verified by test coordinator',
                            answers=[dict(questionId='verify', revision=1,
                                          freeText='Verify identity only for restricted products.')])
            resolved = cli('resolve', dict(presented=presented, response=response))
            self.assertEqual(resolved['registration'], 'caller_required')
            self.assertFalse(resolved['gateAuthority'])
            self.assertFalse(resolved['authenticated'])
            self.assertEqual(resolved['answers'][0]['freeText'], response['answers'][0]['freeText'])

            # Model a coordinator's confirmed atomic save, then a crash before continuation.
            record = evidence / 'checkout-answer.json'
            temporary = evidence / 'checkout-answer.pending'
            temporary.write_text(json.dumps(resolved['receipt']))
            os.replace(temporary, record)
            # A new interpreter reads the real record after an unknown previous write outcome.
            resumed = cli('resolve', dict(presented=presented, response=response,
                                          receipts=[json.loads(record.read_text())]))
            self.assertEqual(resumed['status'], 'no_op')
            self.assertEqual(resumed['answers'], [])
            self.assertEqual(resumed['unresolvedQuestionIds'], [])
            # Coordinator deliberately revalidates the prerequisite before opening its child.
            batch['resolvedQuestionIds'] = ['verify']
            child = cli('prepare', dict(batch=batch, capabilities=capabilities))
            self.assertEqual([q['id'] for q in child['questions']], ['notify'])
            cli('resolve', dict(presented=child, response=response), expected=2)
            self.assertEqual(json.loads(record.read_text()), resolved['receipt'])
            self.assertEqual(ledger.read_bytes(), original)
