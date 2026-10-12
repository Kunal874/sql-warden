import json

import pytest

from scripts.run_e9 import check_evaluation_env, load_generators, validate_done


@pytest.fixture
def evaluation_files(tmp_path, monkeypatch):
    from scripts import run_e9

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/g6-serving-manifest.json").write_text(
        json.dumps(serving_manifest()), encoding="utf-8"
    )
    (tmp_path / "uv.lock").write_text("fixed-lock", encoding="utf-8")
    monkeypatch.setattr(run_e9, "ROOT", tmp_path)
    monkeypatch.setattr(run_e9, "RAW", tmp_path / "raw")
    monkeypatch.setattr(run_e9, "check_e9_resources", lambda **kwargs: None, raising=False)
    monkeypatch.setattr(run_e9.os, "environ", {})
    monkeypatch.setattr(run_e9, "build_items", lambda split: [{"question_id": 1}])
    monkeypatch.setattr(
        run_e9,
        "manifest_for",
        lambda *args: {
            "fingerprint": "old",
            "models": {"arctic": "legacy"},
            "git": {"commit": "clean", "dirty": False},
        },
    )

    async def infer(item, condition, values, cache, lock, *, generator):
        assert cache is None
        return {
            "question_id": item["question_id"],
            "condition": condition,
            "status": "answered",
            "gold_corrected_valid": True,
            "final_ex_corrected": 1,
        }

    monkeypatch.setattr(run_e9, "run_item", infer)
    return tmp_path


async def test_e9_metadata_names_only_the_actual_generator(evaluation_files):
    from scripts.run_e9 import run

    await run("tuned", "dev", resume=False)
    metadata = json.loads((evaluation_files / "raw/dev/tuned.manifest.json").read_text())
    assert metadata["models"] == {"tuned": "b" * 64}
    records = (evaluation_files / "raw/dev/tuned.jsonl").read_text().splitlines()
    assert json.loads(records[0])["generator"] == "tuned"


async def test_e9_resume_does_not_repeat_completed_inference(evaluation_files, monkeypatch):
    from scripts import run_e9

    await run_e9.run("base", "dev", resume=False)
    before = (evaluation_files / "raw/dev/base.jsonl").read_bytes()

    async def unexpected(*args, **kwargs):
        pytest.fail("completed inference repeated")

    monkeypatch.setattr(run_e9, "run_item", unexpected)
    await run_e9.run("base", "dev", resume=True)
    assert (evaluation_files / "raw/dev/base.jsonl").read_bytes() == before


async def test_e9_refuses_partial_tail_without_modifying_it(evaluation_files):
    from scripts.run_e9 import run

    await run("base", "dev", resume=False)
    path = evaluation_files / "raw/dev/base.jsonl"
    path.write_bytes(path.read_bytes() + b'{"question_id":')
    before = path.read_bytes()
    with pytest.raises(json.JSONDecodeError):
        await run("base", "dev", resume=True)
    assert path.read_bytes() == before


async def test_e9_refuses_complete_unterminated_tail_before_new_inference(
    evaluation_files, monkeypatch
):
    from scripts import run_e9

    await run_e9.run("base", "dev", resume=False)
    path = evaluation_files / "raw/dev/base.jsonl"
    path.write_bytes(path.read_bytes().rstrip(b"\n"))
    before = path.read_bytes()
    monkeypatch.setattr(
        run_e9, "build_items", lambda split: [{"question_id": 1}, {"question_id": 2}]
    )
    calls = []

    async def unexpected(*args, **kwargs):
        calls.append("inference")
        return {
            "question_id": 2,
            "status": "answered",
            "gold_corrected_valid": True,
            "final_ex_corrected": 1,
        }

    monkeypatch.setattr(run_e9, "run_item", unexpected)
    with pytest.raises(ValueError, match="unterminated"):
        await run_e9.run("base", "dev", resume=True)
    assert not calls
    assert path.read_bytes() == before


async def test_e9_budget_exhaustion_before_start_writes_nothing(evaluation_files, monkeypatch):
    from scripts import run_e9

    def exhausted(**kwargs):
        raise RuntimeError("budget exhausted")

    monkeypatch.setattr(run_e9, "check_e9_resources", exhausted)
    with pytest.raises(RuntimeError, match="budget exhausted"):
        await run_e9.run("base", "dev", resume=False)
    assert not (evaluation_files / "raw").exists()


@pytest.mark.parametrize("stage", ["before_inference", "before_append"])
async def test_e9_mid_run_budget_exhaustion_preserves_evidence(
    evaluation_files, monkeypatch, stage
):
    from scripts import run_e9

    await run_e9.run("base", "dev", resume=False)
    path = evaluation_files / "raw/dev/base.jsonl"
    before = path.read_bytes()
    monkeypatch.setattr(
        run_e9, "build_items", lambda split: [{"question_id": 1}, {"question_id": 2}]
    )
    calls = []
    sizes = []
    checks = []

    async def infer(*args, **kwargs):
        calls.append("inference")
        return {
            "question_id": 2,
            "status": "answered",
            "gold_corrected_valid": True,
            "final_ex_corrected": 1,
        }

    def budget(*, planned_bytes=0):
        checks.append(planned_bytes)
        if stage == "before_inference" and len(checks) > 1:
            raise RuntimeError("budget exhausted")
        if stage == "before_append" and planned_bytes:
            sizes.append(planned_bytes)
            raise RuntimeError("budget exhausted")

    monkeypatch.setattr(run_e9, "run_item", infer)
    monkeypatch.setattr(run_e9, "check_e9_resources", budget)
    with pytest.raises(RuntimeError, match="budget exhausted"):
        await run_e9.run("base", "dev", resume=True)
    assert calls == (["inference"] if stage == "before_append" else [])
    if stage == "before_append":
        assert sizes[0] > 0
    assert path.read_bytes() == before


def serving_manifest():
    return {
        name: {
            "name": name,
            "alias": f"sqlwarden-{name}:e9-v1",
            "digest": digit * 64,
            "context_tokens": 8192,
            "max_output_tokens": 3072,
            "quantization": "Q4_K_M",
        }
        for name, digit in [("base", "a"), ("tuned", "b")]
    }


@pytest.mark.parametrize("repairs", [0, 1])
async def test_dev_repair_runs_are_separate_from_completed_e9(evaluation_files, repairs):
    from scripts.run_e9 import run

    await run("tuned", "dev", resume=False, dev_repairs=repairs)
    path = evaluation_files / f"raw/repair/dev/k{repairs}.jsonl"
    row = json.loads(path.read_text())
    assert row["experiment"] == "E10-dev-repair"
    assert row["generator"] == "tuned"
    assert row["condition"] == ("full_n1_k1" if repairs else "full_n1")
    manifest = json.loads(path.with_suffix(".manifest.json").read_text())
    assert manifest["experiment"] == "E10-dev-repair"
    assert not (evaluation_files / "raw/dev/tuned.jsonl").exists()


@pytest.mark.parametrize(
    "model,split,repairs", [("base", "dev", 1), ("tuned", "held_out", 1), ("tuned", "dev", 2)]
)
async def test_dev_repair_scope_refused_before_writes(evaluation_files, model, split, repairs):
    from scripts.run_e9 import run

    with pytest.raises(ValueError, match="development repair"):
        await run(model, split, resume=False, dev_repairs=repairs)
    assert not (evaluation_files / "raw").exists()


def test_models_must_have_matching_fixed_inference_budgets(tmp_path):
    manifest = serving_manifest()
    manifest["tuned"]["max_output_tokens"] = 512
    path = tmp_path / "serving.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="contract"):
        load_generators(path)


def test_serving_models_load_as_distinct_pinned_generators(tmp_path):
    path = tmp_path / "serving.json"
    path.write_text(json.dumps(serving_manifest()), encoding="utf-8")
    models = load_generators(path)
    assert models["base"].digest != models["tuned"].digest
    assert models["base"].context_tokens == models["tuned"].context_tokens


@pytest.mark.parametrize(
    "records", [[{"question_id": 1}, {"question_id": 1}], [{"question_id": 9}]]
)
def test_resume_refuses_duplicate_or_unknown_question_ids(records):
    with pytest.raises(ValueError, match="records"):
        validate_done(records, [1, 2])


def test_completed_ids_can_resume_without_repeating_them():
    assert validate_done([{"question_id": 1}], [1, 2]) == {1}


@pytest.mark.parametrize("key", ["WARDEN_BOOTSTRAP_PASSWORD", "WARDEN_TEST_TARGET", "PGPASSWORD"])
def test_setup_credentials_refuse_evaluation_startup(key):
    with pytest.raises(ValueError, match="setup"):
        check_evaluation_env({key: "fake-value"})
