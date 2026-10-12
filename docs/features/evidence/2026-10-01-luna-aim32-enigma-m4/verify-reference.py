"""Read-only checks of frozen M3/M4 reference data and recorded M4 candidates.

Requires py-enigma==1.0.2. Does not execute either product or reproduce runtime.
The single invalid Luna-only candidate is an expected finding, not a failure
of this replay. A changed result, score, token calculation or payload fails.
"""
import hashlib
import json
import math
import statistics
from decimal import Decimal, ROUND_HALF_UP
from importlib.metadata import version
from pathlib import Path

from enigma.machine import EnigmaMachine

ROOT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / name).read_text())


def machine(rotors, reflector, rings, start, plugboard):
    result = EnigmaMachine.from_key_sheet(
        rotors=" ".join(rotors), reflector=reflector,
        ring_settings=" ".join(rings),
        plugboard_settings="" if plugboard == "Inga par" else plugboard,
    )
    result.set_display(start)
    return result


def main():
    assert version("py-enigma") == "1.0.2", "Use the pinned reference."
    summary = load("summary.json")
    for name, expected in summary["publicEvidenceSha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    m3 = load("../2026-09-30-luna-aim32-enigma/vectors.json")
    for row in m3:
        config = row["config"]
        reference = machine(config["rotors"], config["reflector"], config["rings"],
                            config["positions"], config["plugboard"])
        assert reference.process_text(row["plaintext"]) == row["ciphertext"], row["id"]
        if "final" in row:
            assert reference.get_display() == row["final"], row["id"]
    m4 = load("m4-vectors.json")["vectors"]
    for row in m4:
        reference = machine(row["rotors"], row["reflector"], row["rings"],
                            row["start"], " ".join(row["plugboard"]))
        assert reference.process_text(row["plain"]) == row["cipher"], row["id"]
        assert reference.get_display() == row["final"], row["id"]
    assert len(m3) == 123 and len(m4) == 120
    results = load("m4-known-answer-results.json")
    for stage, rows in (("M3", m3), ("M4", m4)):
        for variant in ("aim", "naked"):
            assert results[stage][variant] == {
                "total": len(rows), "passed": len(rows), "mismatches": []}
    print(f"Frozen reference answers verified: {len(m3) + len(m4)}/243")

    cases = {row["id"]: row for row in load("m4-cases.json")["cases"]}
    validation = load("m4-candidate-validation.json")
    for variant in ("aim", "naked"):
        checked = valid = previews = positive = 0
        invalid = []
        for path in sorted(ROOT.glob(f"m4-search-{variant}-*-1.json")):
            result = json.loads(path.read_text())
            case = cases[result["id"]]
            assert result["returned"] == len(result["candidates"]), path.name
            has_valid = False
            for candidate in result["candidates"]:
                reference = machine(case["rotors"], case["reflector"], case["rings"],
                                    candidate["positions"], candidate["plugboard"])
                plaintext = reference.process_text(case["ciphertext"])
                offset = candidate["placement"]
                matches = plaintext[offset:offset + len(case["crib"])] == case["crib"]
                preview_matches = plaintext == candidate["preview"]
                checked += 1
                valid += matches
                previews += preview_matches
                has_valid |= matches
                if not matches or not preview_matches:
                    invalid.append({"case": case["id"], "positions": candidate["positions"],
                                    "offset": offset, "valid": matches,
                                    "previewMatches": preview_matches})
            if case["id"] in summary["newPositiveSearchCases"]:
                positive += has_valid
        actual = {"checked": checked, "valid": valid,
                  "previewMatches": previews, "invalid": invalid}
        assert actual == validation[variant] == summary["returnedCandidatesValidated"][variant]
        assert positive == summary["newPositiveSearchCasesWithValidCandidate"][variant]
        print(f"{variant}: {valid}/{checked} valid recorded candidates; {positive}/8 positive cases")

    benchmark = load("benchmark.json")
    for variant in ("aim", "naked"):
        expected = benchmark["variants"][variant]
        rows = [load(name) for name in expected["rawResults"]]
        assert [row["run"] for row in rows] == [1, 2, 3, 4]
        assert all(row["status"] == "complete" and row["checked"] == 17576
                   and row["returned"] == 2 for row in rows)
        assert rows[0]["elapsedSeconds"] == expected["warmupSeconds"]
        measured = [row["elapsedSeconds"] for row in rows[1:]]
        assert measured == expected["measuredSeconds"]
        assert statistics.median(measured) == expected["medianSeconds"]
    ratio = benchmark["variants"]["naked"]["medianSeconds"] / benchmark["variants"]["aim"]["medianSeconds"]
    assert ratio == benchmark["runtimeRatioNakedOverAim"]
    assert benchmark == summary["applicationRuntime"]
    print(f"Recorded complete-search runtime ratio verified: {ratio:.1f}x")

    assert sum(row["weightPercent"] for row in summary["kpis"]) == 100
    for variant in ("aim", "naked"):
        score = sum(Decimal(str(row[variant])) * row["weightPercent"] / 10
                    for row in summary["kpis"])
        assert float(score) == summary["weightedScoreExact"][variant]
        rounded = score.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        assert float(rounded) == summary["publishedScoreOutOf100"][variant]
    cost = load("m4-token-cost.json")
    for variant in ("aim", "naked"):
        sessions = [cost["sessions"][name] for name in
                    (("aim_main", "aim_reviewer") if variant == "aim" else ("naked_main",))]
        for key in ("input_tokens", "cached_input_tokens", "uncached_input_tokens", "output_tokens"):
            assert sum(row[key] for row in sessions) == cost[variant][key]
        assert cost[variant]["input_tokens"] == cost[variant]["uncached_input_tokens"] + cost[variant]["cached_input_tokens"]
        for rate_key, total_key in (("credits_per_million", "credits_per_million"),
                                    ("api_usd_per_million", "api_usd_per_million")):
            total = sum(cost[variant][token] * cost["pricing"][rate_key][rate] / 1_000_000
                        for token, rate in (("uncached_input_tokens", "uncached_input"),
                                            ("cached_input_tokens", "cached_input"),
                                            ("output_tokens", "output")))
            assert math.isclose(total, cost[variant][total_key], abs_tol=1e-12)
    for field, total_key, summary_key in (
        ("extra_aim_credits", "credits_per_million", "extraAimStandardCredits"),
        ("extra_aim_api_usd_equivalent", "api_usd_per_million", "extraAimApiUsdEquivalent"),
    ):
        delta = cost["aim"][total_key] - cost["naked"][total_key]
        assert math.isclose(delta, cost["comparison"][field], abs_tol=1e-12)
        assert math.isclose(delta, summary["m4TokenCost"][summary_key], abs_tol=1e-12)
    print("Score arithmetic, token calculation and public payload hashes verified.")


if __name__ == "__main__":
    main()
