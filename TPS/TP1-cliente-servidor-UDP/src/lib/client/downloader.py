from lib.client.file_transfer import FileTransfer
from lib.common.constants import OP_DOWNLOAD


class Downloader(FileTransfer):

    def __init__(self, protocol, verbose, quiet):
        super().__init__(protocol, verbose, quiet)

    def run(self, filepath, filename):
        self.log.print(
            f"Iniciando descarga de archivo '{filename}' del servidor {self.protocol.addr}:{self.protocol.port}"
        )
        try:
            self._start_threads()
            self.protocol.start_handshake(
                self.in_queue,
                self.sender_queue,
                OP_DOWNLOAD,
                filepath,
                filename,
                self.verbose,
                self.quiet,
            )
            self.protocol.receive_file(
                filepath,
                filename,
                (self.protocol.addr, self.protocol.port),
                self.in_queue,
                self.sender_queue,
            )
            self.sender_queue.join()
            self._log_transfer_time()
            return True
        finally:
            self._cleanup()
