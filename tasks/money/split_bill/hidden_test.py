from decimal import Decimal

from solution import split_bill


def test_even_split():
    assert split_bill("10.00", 4) == ["2.50", "2.50", "2.50", "2.50"]


def test_thirds():
    assert split_bill("100.00", 3) == ["33.34", "33.33", "33.33"]


def test_tiny_amounts():
    assert split_bill("0.10", 3) == ["0.04", "0.03", "0.03"]
    assert split_bill("0.01", 2) == ["0.01", "0.00"]


def test_one_person():
    assert split_bill("57.31", 1) == ["57.31"]


def test_sum_is_exact_for_large_total():
    shares = split_bill("1234567.89", 7)
    assert sum(Decimal(s) for s in shares) == Decimal("1234567.89")
    assert len(shares) == 7


def test_shares_differ_by_at_most_one_cent_and_descend():
    shares = [Decimal(s) for s in split_bill("20.05", 6)]
    assert max(shares) - min(shares) <= Decimal("0.01")
    assert shares == sorted(shares, reverse=True)
    assert sum(shares) == Decimal("20.05")
