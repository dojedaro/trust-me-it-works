from solution import merge_intervals


def test_overlap_and_order():
    assert merge_intervals([(1, 3), (2, 4)]) == [(1, 4)]
    assert merge_intervals([(5, 6), (1, 2)]) == [(1, 2), (5, 6)]
    assert merge_intervals([]) == []


def test_touching_intervals_merge():
    assert merge_intervals([(1, 3), (3, 5)]) == [(1, 5)]
    assert merge_intervals([(1, 2), (2, 2), (2, 3)]) == [(1, 3)]


def test_containment():
    assert merge_intervals([(1, 5), (2, 3)]) == [(1, 5)]


def test_empty_and_reversed_are_dropped():
    assert merge_intervals([(3, 3), (1, 2)]) == [(1, 2)]
    assert merge_intervals([(4, 1)]) == []
    assert merge_intervals([(1, 2), (5, 1), (3, 4)]) == [(1, 2), (3, 4)]


def test_input_is_not_modified_and_lists_are_accepted():
    data = [[3, 4], [1, 2]]
    assert merge_intervals(data) == [(1, 2), (3, 4)]
    assert data == [[3, 4], [1, 2]]
