class VerboseLogger:
    def __init__(self, verbose=False):
        self.verbose = verbose

    def print(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)


_logger = VerboseLogger()


def verbose_print(*args, **kwargs):
    _logger.print(*args, **kwargs)


def set_verbose(enabled=False):
    _logger.verbose = enabled
