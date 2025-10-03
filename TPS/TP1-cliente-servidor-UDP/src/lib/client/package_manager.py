from lib.common.log import Log


class PackageManager:
    def __init__(self, in_queue, verbose=False, quiet=False):
        self.in_queue = in_queue
        self.log = Log("PACKAGE MANAGER", verbose, quiet)
        self.verbose = verbose
        self.quiet = quiet

    def handle_new_package(self, addr, data):
        self.in_queue.put((addr, data))
