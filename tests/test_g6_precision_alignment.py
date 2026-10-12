import struct

import pytest

from scripts.prepare_g6_serving import fp16_rounding_changes


def test_only_exact_fp16_rounding_is_accepted():
    original = struct.pack("<3f", 1.0, 2**-25, -(2**-25))
    rounded = struct.pack("<3f", 1.0, 0.0, -0.0)
    assert fp16_rounding_changes(original, rounded) == 2


@pytest.mark.parametrize(
    "original,rounded",
    [
        (struct.pack("<f", 1.0), struct.pack("<f", 2.0)),
        (struct.pack("<f", float("nan")), struct.pack("<f", float("nan"))),
        (b"bad", b"bad"),
        (struct.pack("<f", 1.0), b""),
    ],
)
def test_arbitrary_changes_or_invalid_values_are_not_rounding(original, rounded):
    with pytest.raises(ValueError, match="rounding"):
        fp16_rounding_changes(original, rounded)
