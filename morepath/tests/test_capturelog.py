import logging


from .capturelog import CaptureLog


def test_basic():
    logger = logging.getLogger('experiment')

    with CaptureLog('experiment') as captured:
        logger.warning("Hello")

    assert len(captured.records) == 1
    assert captured.records[0].name == 'experiment'
    assert captured.records[0].msg == "Hello"
    assert captured.records[0].getMessage() == "Hello"


def test_record_tuples():
    logger = logging.getLogger('experiment')

    with CaptureLog('experiment') as captured:
        logger.warning("Hello")

    assert len(captured.record_tuples) == 1
    assert captured.record_tuples[0] == ('experiment',
                                         logging.WARNING,
                                         "Hello")


def test_different_name():
    logger = logging.getLogger('experiment')

    with CaptureLog('different') as captured:
        logger.warning("Hello")

    assert len(captured.records) == 0


def test_name_prefix():
    logger = logging.getLogger('prefix.experiment')

    with CaptureLog('prefix') as captured:
        logger.warning("Hello")

    assert len(captured.records) == 1


def test_default_level():
    logger = logging.getLogger('experiment')

    with CaptureLog('experiment') as captured:
        logger.warning("Captured")
        logger.debug("Not captured")

    assert len(captured.records) == 1
    assert captured.records[0].msg == "Captured"


def test_change_level():
    logger = logging.getLogger('experiment')

    with CaptureLog('experiment', logging.DEBUG) as captured:
        logger.warning("Captured")
        logger.debug("Also captured")

    assert len(captured.records) == 2
    assert captured.records[0].msg == "Captured"
    assert captured.records[1].msg == "Also captured"
