import threading
from lib.common.constants import (
    QUEUE_FINISHED_CLIENTS,
    SENDER_QUEUE,
    OP_DOWNLOAD,
    OP_UPLOAD,
)
import queue
from lib.common.log import Log

TIMEOUT_SECONDS = 1.0


class ClientHandler(threading.Thread):
    def __init__(
        self,
        verbose,
        quiet,
        server_queues,
        operation,
        client_addr,
        protocol,
        filepath,
        filename,
        storage_path,
    ):
        super().__init__()
        self.server_queues = server_queues
        self.operation = operation
        self.client_addr = client_addr
        self.protocol = protocol
        self.filepath = filepath
        self.filename = filename
        self.storage_path = storage_path
        self.in_queue = queue.Queue()
        self.running = True
        self.log = Log("CLIENT HANDLER", verbose, quiet)
        self.log.debug(
            f"Hilo iniciado para {self.client_addr} con protocolo {protocol.NAME}"
        )

    def run(self):
        """Lanza el handler y maneja la operación correspondiente para
        el cliente (upload o download). Si la operación no es soportada,
        se cierra el hilo."""

        self.log.debug(f"\n")
        if self.operation == OP_DOWNLOAD:
            self.log.debug(
                f"SE INICIA PROCESO DE DESCARGA DE ARCHIVO DEL CLIENTE: {self.client_addr}"
            )
            self.run_download()
        elif self.operation == OP_UPLOAD:

            self.log.debug(
                f"SE INICIA PROCESO DE GUARDADO DE ARCHIVO DEL CLIENTE: {self.client_addr}"
            )
            self.run_upload()
        else:
            self.log.debug(f"Operacion no soportada: {self.operation}")
            self.running = False

    def run_download(self):
        """Maneja la operación de descarga. Envia el archivo solicitado por el cliente."""
        try:
            self.protocol.send_file(
                self.storage_path,
                self.filename,
                self.client_addr,
                self.in_queue,
                self.server_queues[SENDER_QUEUE],
            )
        except Exception as e:
            self.log.debug(f"Ocurrio un error durante la transferencia: {e}")
        self._finish_client()

    def run_upload(self):
        """Maneja la operación de subida. Recibe el archivo enviado por el cliente."""
        try:
            # Usar el método unificado receive_file
            self.protocol.receive_file(
                self.storage_path,
                self.filename,
                self.client_addr,
                self.in_queue,
                self.server_queues[SENDER_QUEUE],
            )
        except Exception as e:
            self.log.debug(f"Ocurrió un error durante la transferencia: {e}")
        finally:
            self._finish_client()

    def send(self, message):
        self.in_queue.put((self.client_addr, message))

    def _finish_client(self):
        """Agrega el cliente a la cola de clientes finalizados para que el
        servidor pueda limpiarlo."""
        self.server_queues[QUEUE_FINISHED_CLIENTS].put(self.client_addr)
        self.log.debug(f"\n")
        self.log.debug(f"Hilo terminado para {self.client_addr}")
