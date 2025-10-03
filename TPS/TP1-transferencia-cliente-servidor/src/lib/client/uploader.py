from lib.client.file_transfer import FileTransfer
from lib.common.constants import OP_UPLOAD


class Uploader(FileTransfer):

    def __init__(self, protocol, verbose, quiet):
        super().__init__(protocol, verbose, quiet)

    def run(self, filepath, filename):
        self.log.print(
            f"Iniciando subida de archivo '{filename}' al servidor {self.protocol.addr}:{self.protocol.port}"
        )

        try:
            self._start_threads()
            self.protocol.start_handshake(
                self.in_queue,
                self.sender_queue,
                OP_UPLOAD,
                filepath,
                filename,
                self.verbose,
                self.quiet,
            )
            self.protocol.send_file(
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
