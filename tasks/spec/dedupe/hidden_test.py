from solution import dedupe


def test_numbers_keep_first_order():
    assert dedupe([3, 1, 3, 2, 1]) == [3, 1, 2]


def test_unhashable_lists():
    assert dedupe([[1], [1], [2]]) == [[1], [2]]


def test_unhashable_dicts():
    assert dedupe([{"a": 1}, {"a": 1}, {"b": 2}]) == [{"a": 1}, {"b": 2}]


def test_mixed_types():
    assert dedupe(["a", [1], "a", [1], 2]) == ["a", [1], 2]


def test_empty():
    assert dedupe([]) == []


def test_returns_new_list():
    items = [1, 2]
    assert dedupe(items) is not items
