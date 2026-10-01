"""Read-only replay of public Enigma vectors and recorded search candidates.

Requires py-enigma==1.0.2. Does not execute either product or reproduce runtime.
"""
import hashlib
import json
from importlib.metadata import version
from pathlib import Path

from enigma.machine import EnigmaMachine

ROOT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / name).read_text())


def machine(config, positions, plugboard):
    result = EnigmaMachine.from_key_sheet(
        rotors=" ".join(config["rotors"]), reflector=config["reflector"],
        ring_settings=" ".join(config["rings"]), plugboard_settings=plugboard,
    )
    result.set_display(positions)
    return result


def main():
    assert version("py-enigma") == "1.0.2", "Use the comparison's pinned reference."
    summary = load("summary.json")
    for name, expected in summary["publicEvidenceSha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    vectors = load("vectors.json")
    for vector in vectors:
        config = vector["config"]
        reference = machine(config, config["positions"], config["plugboard"])
        assert reference.process_text(vector["plaintext"]) == vector["ciphertext"], vector["id"]
        if "final" in vector:
            assert reference.get_display() == vector["final"], vector["id"]
    print(f"Frozen reference answers verified: {len(vectors)}/{len(vectors)}")
    cases = {case["id"]: case for case in load("cases.json")}
    for name, ciphertext, crib in (
        ("aim", "CLURUKKAWSAUVYUKQKINTOGFJK", "WEATTACKATDAWNFROMTHENORTH"),
        ("naked", "CLLRHUUZBBWYISFLTXOUWOBLVBMZNETVFUMYWDRW", "WETTERBERICHTAUSBERLINMELDETSONNENSCHEIN"),
    ):
        cases[f"shared-example-{name}"] = {
            "ciphertext": ciphertext, "crib": crib,
            "config": {"rotors": ["I", "II", "III"], "reflector": "B", "rings": "AAA"},
        }
    expected_validation = load("luna-pair-candidate-validation.json")
    for variant in ("aim", "naked"):
        total = 0
        expected = {record["id"]: record for record in expected_validation[variant]}
        for record in load(f"luna-pair-search-{variant}.json"):
            case = cases[record["id"]]
            candidates = record.get("candidates", [])
            assert len(candidates) == expected[record["id"]]["returned"]
            for candidate in candidates:
                plugboard = candidate["plugboard"]
                reference = machine(case["config"], candidate["positions"], "" if plugboard == "Inga par" else plugboard)
                plaintext = reference.process_text("".join(ch for ch in case["ciphertext"] if "A" <= ch <= "Z"))
                crib = "".join(ch for ch in case["crib"].upper() if "A" <= ch <= "Z")
                offset = candidate["placement"]
                assert plaintext[offset:offset + len(crib)] == crib, record["id"]
                total += 1
        assert total == summary["returnedCandidatesValidated"][variant]["valid"]
        print(f"{variant}: {total}/{total} recorded candidates verified")


if __name__ == "__main__":
    main()
