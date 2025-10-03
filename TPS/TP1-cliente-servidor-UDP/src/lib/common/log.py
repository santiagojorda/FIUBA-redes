class Log:

    def __init__(self, prefix, verbose=False, quiet=False):
        self.verbose = verbose
        self.quiet = quiet
        self.prefix = prefix

        if self.quiet:
            self.verbose = False

    def debug(self, message):
        if self.verbose:
            print(f"[DEBUG] {self.prefix} - {message}")

    def print(self, message):
        print(f"{message}")

    def error(self, message):
        print(f"[ERROR] {self.prefix} - {message}")
