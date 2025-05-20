import re


class RegexStr:
    def __init__(self, pattern):
        self.pattern = re.compile(pattern, re.IGNORECASE)

    def __eq__(self, other):
        return bool(self.pattern.search(other))
