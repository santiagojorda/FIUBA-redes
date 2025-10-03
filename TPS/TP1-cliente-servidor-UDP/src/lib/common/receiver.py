from lib.common.constants import CHUNK_SIZE
from lib.common.log import Log
import threading
import socket

RECV_TIMEOUT = 0.05  # 50 ms


class Receiver(threading.Thread):

    def __init__(self, sock, pkg_manager, verbose, quiet):
        threading.Thread.__init__(self)
        self.sock = sock
        self.running = True
        self.pkg_manager = pkg_manager
        self.log = Log(f"RECEIVER:", verbose, quiet)

    def run(self):
        self.log.debug("Hilo corriendo")
        while self.running:
            try:
                self.sock.settimeout(RECV_TIMEOUT)
                data, client_addr = self.sock.recvfrom(CHUNK_SIZE + 100)
                self.pkg_manager.handle_new_package(client_addr, data)

            except socket.timeout:
                continue

            except OSError as e:
                if e.errno == 9:  # Bad file descriptor - socket cerrado
                    self.log.debug("Socket cerrado, terminando Receiver")
                    break
                else:
                    self.log.error(f"Error de socket: {e}")

            except Exception as e:
                if not self.running:
                    break
                self.log.error(f"Error inesperado al recibir datos: {e}")

    def stop(self):
        self.log.debug("Hilo cerrado")
        self.running = False
