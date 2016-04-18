import warnings


def test_security_to_authentication():
    warnings.simplefilter("always")
    with warnings.catch_warnings(record=True) as w:
        from morepath import security  # noqa
    assert len(w) == 1
    assert w[0].message
