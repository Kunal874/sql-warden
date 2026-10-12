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
