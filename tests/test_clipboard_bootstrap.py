import logging

from project_planner_frontend.bootstrap.CutbufferLogFilter import CutbufferLogFilter


def test_cutbuffer_filter_only_hides_known_optional_provider_probe() -> None:
    log_filter = CutbufferLogFilter()
    cutbuffer = logging.LogRecord(
        "kivy",
        logging.CRITICAL,
        "",
        0,
        "Cutbuffer: Unable to find any valuable Cutbuffer provider. details",
        (),
        None,
    )
    real_failure = logging.LogRecord(
        "kivy",
        logging.CRITICAL,
        "",
        0,
        "Window: Unable to initialize SDL2",
        (),
        None,
    )

    assert log_filter.filter(cutbuffer) is False
    assert log_filter.filter(real_failure) is True
