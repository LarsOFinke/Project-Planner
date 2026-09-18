import logging


class CutbufferLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return not record.getMessage().startswith(
            "Cutbuffer: Unable to find any valuable Cutbuffer provider"
        )
