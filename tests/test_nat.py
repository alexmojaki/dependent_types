from dependent_types import nat
from dependent_types.nat import ZERO


def test_nat():
    five = nat.Nat("5", value=5)
    assert isinstance(five, nat.NatInstance)


def test_successor():
    ONE = nat.successor(ZERO)
    ONE_again = nat.successor(ZERO)
    assert ONE == ONE_again
    print(ONE.value)


def test_add():
    ONE = nat.successor(nat.ZERO)
    TWO = ONE + 1
    THREE = ONE + 2
    FOUR = ONE + 3
    FIVE = ONE + 4

    assert ONE + ONE == TWO
    assert TWO + THREE == FIVE
    assert THREE + TWO == FIVE


def test_mul():
    EIGHT = ZERO + 8
    SEVEN = ZERO + 7
    SIXTY_FOUR = ZERO + 64
    FIFTY_SIX = ZERO + 56

    assert EIGHT * EIGHT == SIXTY_FOUR
    assert EIGHT * SEVEN == FIFTY_SIX
    assert EIGHT * ZERO == ZERO
    assert ZERO * EIGHT == ZERO


def test_comparison():
    assert (ZERO + 6) <= (ZERO + 7)
    assert not (ZERO + 10) <= (ZERO + 7)

    n = nat.Nat("n")
    m = n + 5
    assert n <= m
    assert m >= n
    assert not n >= m


def test_variable_addition():
    n = nat.Nat("n")
    m = nat.Nat("m")
    k = n + m

    assert k.value == (None, nat.add, (n, m), {})


def test_variable_multiplication():
    n = nat.Nat("n")
    m = nat.Nat("m")
    k = n * m

    assert k.value == (None, nat.mul, (n, m), {})
