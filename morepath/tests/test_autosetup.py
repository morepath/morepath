from morepath.autosetup import morepath_modules

def test_import():
    import base, sub
    from ns import real
    assert sorted(list(morepath_modules()),
                  key=lambda module: module.__name__) == [base, real, sub]
