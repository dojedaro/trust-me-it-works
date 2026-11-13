from solution import allocate


def raises(fn, *args):
    """True if fn(*args) raises ValueError. Hidden tests use the standard library only."""
    try:
        fn(*args)
    except ValueError:
        return True
    return False


def test_even_split_and_examples():
    assert allocate(100, [1, 1, 1]) == [34, 33, 33]
    assert allocate(5, [1, 0, 1]) == [3, 0, 2]
    assert allocate(1000, [1, 2, 3, 4]) == [100, 200, 300, 400]


def test_largest_remainder_wins():
    assert allocate(101, [3, 7]) == [30, 71]
    assert allocate(7, [1, 1, 1]) == [3, 2, 2]


def test_ties_go_to_the_earlier_part():
    assert allocate(10, [3, 1]) == [8, 2]
    assert allocate(1, [1, 1, 1, 1]) == [1, 0, 0, 0]


def test_negative_total():
    assert allocate(-100, [1, 1, 1]) == [-34, -33, -33]


def test_zero_weights():
    assert allocate(7, [0, 0, 5]) == [0, 0, 7]
    assert allocate(0, [1, 2]) == [0, 0]
    assert raises(allocate, 5, [0, 0])


def test_exact_with_huge_totals():
    assert allocate(10**17 + 3, [1, 2]) == [33333333333333334, 66666666666666669]
