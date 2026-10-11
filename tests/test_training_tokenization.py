import pytest

from training.tokenize_records import balanced_sample, tokenize


def test_sampling_keeps_each_database_before_second_examples():
    rows = [{"source_index": i, "db_id": "a"} for i in range(4)]
    rows.append({"source_index": 4, "db_id": "b"})
    selected = balanced_sample(rows, limit=2)
    assert len(selected) == 2
    assert {row["db_id"] for row in selected} == {"a", "b"}
    assert selected == balanced_sample(list(reversed(rows)), limit=2)


def test_all_overlong_examples_fail_instead_of_training_on_nothing():
    class Tokenizer:
        eos_token = "<end>"
        pad_token_id = 0

        def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
            assert tokenize and add_generation_prompt
            return [10, 11, 12, 13]

        def encode(self, completion, *, add_special_tokens):
            assert completion.endswith("<end>")
            assert not add_special_tokens
            return [20, 21]

    with pytest.raises(ValueError, match="no examples"):
        tokenize(
            [{"source_index": 1, "db_id": "a", "messages": [], "completion": "answer"}],
            Tokenizer(),
            max_length=5,
        )
