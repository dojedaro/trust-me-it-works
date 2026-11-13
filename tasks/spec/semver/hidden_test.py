from solution import compare_versions

CHAIN = [
    "1.0.0-alpha",
    "1.0.0-alpha.1",
    "1.0.0-alpha.beta",
    "1.0.0-beta",
    "1.0.0-beta.2",
    "1.0.0-beta.11",
    "1.0.0-rc.1",
    "1.0.0",
]


def test_core_is_numeric():
    assert compare_versions("1.2.10", "1.2.9") == 1
    assert compare_versions("2.0.0", "10.0.0") == -1
    assert compare_versions("1.2.3", "1.2.3") == 0


def test_spec_precedence_chain():
    for lower, higher in zip(CHAIN, CHAIN[1:]):
        assert compare_versions(lower, higher) == -1, (lower, higher)
        assert compare_versions(higher, lower) == 1, (higher, lower)


def test_build_metadata_is_ignored():
    assert compare_versions("1.0.0+build.1", "1.0.0+build.2") == 0
    assert compare_versions("1.0.0-alpha+001", "1.0.0-alpha") == 0


def test_numeric_identifiers_sort_low_and_ascii_order():
    assert compare_versions("1.0.0-1", "1.0.0-a") == -1
    assert compare_versions("1.0.0-rc.1", "1.0.0-RC.1") == 1


def test_hyphens_inside_prerelease():
    assert compare_versions("1.0.0-x-y.1", "1.0.0-x-y.2") == -1
