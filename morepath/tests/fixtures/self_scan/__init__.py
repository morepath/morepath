def get_this_package():
    from morepath.autosetup import caller_package
    return caller_package(1)


def do_scan():
    import morepath
    morepath.scan()
