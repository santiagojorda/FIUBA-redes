from lib.common import package as packageLib
from lib.server.client_handler import QUEUE_FINISHED_CLIENTS, ClientHandler
from lib.common.protocol_factory import ProtocolFactory
from lib.common.log import Log
from lib.common.constants import SENDER_QUEUE


class ClientManager:
    def __init__(
        self, addr, port, storage_path, server_queues, sock, verbose=False, quiet=False
    ):
        self.addr = addr
        self.port = port
        self.storage_path = storage_path
        self.server_queues = server_queues
        self.sock = sock
        self.log = Log("CLIENT MANAGER", verbose, quiet)
        self.verbose = verbose
        self.quiet = quiet
        self.clients = {}

    def handle_new_package(self, client_addr, data):
        if client_addr in self.clients:
            self.clients[client_addr].send(data)
            return

        if not packageLib.is_handshake_packet(data):
            self.log.debug("Paquete recibido no es handshake")
            return

        self._create_client(client_addr, data)

    def _create_client(self, client_addr, data):
        pkg = packageLib.parse_packet(data)
        if not pkg:
            raise ValueError("Error parseando paquete de handshake")

        protocol, operation, filepath, filename = packageLib.parse_handshake_payload(
            packageLib.get_payload(pkg)
        )

        protocol = ProtocolFactory.create_protocol(
            protocol,
            self.addr,
            self.port,
            self.verbose,
            self.quiet,
        )
        self.server_queues[SENDER_QUEUE].put(
            (packageLib.create_ack_handshake_packet(), client_addr)
        )
        self.log.print(
            f"Nuevo cliente conectado: {client_addr} con protocolo: {protocol.NAME} | operacion: {operation}"
        )
        self.log.debug("Handshake exitoso")

        client_thread = ClientHandler(
            self.verbose,
            self.quiet,
            self.server_queues,
            operation,
            client_addr,
            protocol,
            filepath,
            filename,
            self.storage_path,
        )
        client_thread.start()
        self.clients[client_addr] = client_thread

    def cleanup_finished_clients(self):
        while not self.server_queues[QUEUE_FINISHED_CLIENTS].empty():
            client_addr = self.server_queues[QUEUE_FINISHED_CLIENTS].get()
            if client_addr in self.clients:
                self.clients[client_addr].running = False
                self.clients[client_addr].join()
                del self.clients[client_addr]
                self.log.print(f"Cliente desconectado {client_addr}")

    def shutdown_all_clients(self):
        self.log.print("Cerrando conexiones de clientes...")
        for client_thread in self.clients.values():
            client_thread.running = False
            client_thread.join()
        self.clients.clear()
