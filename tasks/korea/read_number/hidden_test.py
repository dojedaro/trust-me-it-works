from solution import read_number


def test_small_numbers():
    assert read_number(0) == "영"
    assert read_number(7) == "칠"
    assert read_number(10) == "십"
    assert read_number(11) == "십일"
    assert read_number(2026) == "이천이십육"


def test_man_alone_has_no_il():
    assert read_number(10000) == "만"
    assert read_number(11000) == "만천"
    assert read_number(10010) == "만십"


def test_eok_keeps_il():
    assert read_number(100000000) == "일억"
    assert read_number(100010000) == "일억만"


def test_empty_groups_disappear():
    assert read_number(100000001) == "일억일"
    assert read_number(1000000) == "백만"
    assert read_number(210000) == "이십일만"


def test_largest():
    assert read_number(999999999999) == "구천구백구십구억구천구백구십구만구천구백구십구"


def test_silent_one_inside_groups():
    assert read_number(1111) == "천백십일"
    assert read_number(11110000) == "천백십일만"
