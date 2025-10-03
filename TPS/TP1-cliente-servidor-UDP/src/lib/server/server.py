import socket
import queue
from lib.common import constants
from lib.common.constants import QUEUE_FINISHED_CLIENTS, IN_QUEUE, SENDER_QUEUE
import lib.common.args_parser as args_parser
from lib.server.client_manager import ClientManager
from lib.common.log import Log
from lib.common.receiver import Receiver
from lib.common.sender import Sender
import traceback
from time import sleep

CLEAN_TIMEOUT = 2.0


class Server:
    def __init__(self, addr, port, storage_path, verbose=False, quiet=False):
        self.verbose = verbose
        self.quiet = quiet
        self.addr = addr
        self.port = port
        self.storage_path = storage_path
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.running = True
        self.log = Log("SERVER", verbose, quiet)

        self.queues = {
            QUEUE_FINISHED_CLIENTS: queue.Queue(),
            IN_QUEUE: queue.Queue(),
            SENDER_QUEUE: queue.Queue(),
        }

        self.client_manager = ClientManager(
            addr, port, storage_path, self.queues, self.sock, verbose, quiet
        )
        self.receiver = Receiver(
            self.sock, self.client_manager, self.verbose, self.quiet
        )
        self.sender = Sender(
            self.sock, self.queues[SENDER_QUEUE], self.verbose, self.quiet
        )

    def run(self):
        self.log.print(f"Inicializando servidor en {self.addr}:{self.port}")
        self.sock.bind((self.addr, self.port))

        self.receiver.start()
        self.sender.start()

        try:
            while self.running:
                sleep(CLEAN_TIMEOUT)
                self.client_manager.cleanup_finished_clients()

        except KeyboardInterrupt:
            self.log.debug(f"Interrupcion por teclado")
            self.log.debug(f"Cerrando servidor")
        except Exception as e:
            self.log.debug(f"Error inesperado: {e}Traceback:{traceback.format_exc()}")
        finally:
            self.shutdown()

    def shutdown(self):
        self.log.debug("Iniciado apagado...")
        self.running = False
        self.receiver.stop()
        self.sender.stop()
        self.client_manager.shutdown_all_clients()
        self.sock.close()
        self.log.print("Servidor finalizado")


if __name__ == "__main__":
    args = args_parser.parse_server_arguments()
    verbose, quiet, addr, port, storage_path = (
        args.verbose,
        args.quiet,
        args.host,
        args.port,
        constants.STORAGE_PATH,
    )
    server = Server(addr, port, storage_path, verbose, quiet)
    server.run()
