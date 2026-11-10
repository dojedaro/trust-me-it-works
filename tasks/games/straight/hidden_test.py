from solution import straight_high


def test_simple_straight():
    assert straight_high(["9", "T", "J", "Q", "K"]) == "K"


def test_unordered_input():
    assert straight_high(["6", "3", "5", "2", "4"]) == "6"


def test_broadway():
    assert straight_high(["A", "K", "Q", "J", "T"]) == "A"


def test_wheel_is_five_high():
    assert straight_high(["A", "2", "3", "4", "5"]) == "5"
    assert straight_high(["5", "4", "A", "3", "2"]) == "5"


def test_no_wraparound():
    assert straight_high(["Q", "K", "A", "2", "3"]) is None


def test_pair_is_not_straight():
    assert straight_high(["2", "2", "3", "4", "5"]) is None


def test_gap():
    assert straight_high(["2", "3", "4", "5", "7"]) is None
