import os
import time
import socket
import queue
from lib.common.log import Log
from lib.client.package_manager import PackageManager
from lib.common.sender import Sender
from lib.common.receiver import Receiver

START_CONNECTION_TIMEOUT = 5.0


class FileTransfer:
    def __init__(self, protocol, verbose, quiet):
        self.protocol = protocol
        self.log = Log(self.__class__.__name__.upper(), verbose, quiet)
        self.in_queue = queue.Queue()
        self.sender_queue = queue.Queue()
        self.verbose = verbose
        self.quiet = quiet
        self.sock = None
        self.sender = None
        self.receiver = None
        self.start_time = None
        self._setup_connection()

    def _setup_connection(self):
        """Configura la conexión del socket."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(START_CONNECTION_TIMEOUT)

    def _start_threads(self):
        """Inicia los hilos de envío y recepción."""

        if not hasattr(self, "package_manager"):
            self.package_manager = PackageManager(
                self.in_queue, self.verbose, self.quiet
            )

        self.sender = Sender(self.sock, self.sender_queue, self.verbose, self.quiet)
        self.receiver = Receiver(
            self.sock, self.package_manager, self.verbose, self.quiet
        )

        self.sender.start()
        self.receiver.start()
        self.start_time = time.time()

    def _stop_threads(self):
        """Detiene los hilos de envío y recepción."""
        if self.sender:
            self.sender.stop()
        if self.receiver:
            self.receiver.stop()

        if hasattr(self, "sender") and self.sender:
            self.sender.join()
        if hasattr(self, "receiver") and self.receiver:
            self.receiver.join()

    def _cleanup(self):
        """Limpia los recursos."""
        self._stop_threads()
        if self.sock:
            self.sock.close()

    def _get_file_info(self, filepath, filename):
        """Obtiene información del archivo."""
        file_path = os.path.join(filepath, filename)
        file_size = os.path.getsize(file_path)
        self.log.debug(
            f"Ruta del archivo: {file_path} | Tamaño: {file_size / (1024*1024):.2f} MB"
        )
        return file_path, file_size

    def _log_transfer_time(self):
        """Registra el tiempo de transferencia."""
        elapsed_time = time.time() - self.start_time
        self.log.print(f"Tiempo de transferencia: {elapsed_time:.2f} segundos")
        return elapsed_time

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Asegura que los recursos se liberen correctamente."""
        self._cleanup()
