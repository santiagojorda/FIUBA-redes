import queue
from lib.common import package as packageLib
from lib.common.log import Log
from lib.common.constants import CHUNK_SIZE
import os


MAX_RETRIES = 5
TIMEOUT_HANDSHAKE = 1.0


class Protocol:

    def __init__(self, protocol_byte, name, arg_name, host, port, verbose, quiet):
        self.log = Log(self.__class__.__name__.upper(), verbose, quiet)
        self.protocol_byte = protocol_byte
        self.name = name
        self.arg_name = arg_name
        self.addr = host
        self.port = port
        self.verbose = verbose
        self.quiet = quiet

    def receive_file(
        self, filepath, filename, destination_address, in_queue, sender_queue
    ):
        pass

    def _read_file(self, file_path):
        with open(file_path, "rb") as f:
            while True:
                data = f.read(CHUNK_SIZE)
                if not data:
                    break
                yield data

    def _read_file_chunks(self, filepath, filename, destination_address, sender_queue):
        """Función que lee un archivo en chunks de tamaño chunk_size"""
        try:
            file_path = os.path.join(filepath, filename)
            file_size = os.path.getsize(file_path)

            data = list(self._read_file(file_path))
            self._print_file_info(filepath, filename, file_size, len(data))
            return data
        except FileNotFoundError:
            self.log.print(f"No se encontró el archivo {file_path}")
            self._send(
                packageLib.create_fin_packet(), destination_address, sender_queue
            )
            raise
        except Exception as e:
            self.log.debug(f"Error al leer el archivo: {e}")
            raise

    def _send(self, package, addr, sender_queue):
        sender_queue.put((package, addr))

    def _print_file_info(self, filepath, filename, file_size, total_chunks):
        self.log.print(f"Datos del archivo a enviar")
        self.log.print(f"Nombre del archivo: {filename}")
        self.log.print(f"Ruta del a enviar: {filepath}/{filename}")
        self.log.print(f"size del archivo: {file_size / (1024*1024):.2f} MB")
        self.log.print(
            f"Archivo dividido en {total_chunks} chunks de {CHUNK_SIZE} bytes cada uno\n"
        )

    def start_handshake(
        self, in_queue, sender_queue, op, filepath, filename, verbose=False, quiet=False
    ):
        log = Log("HANDSHAKE", verbose, quiet)
        log.debug(f"INICIO")

        pkg = packageLib.create_handshake_packet(
            self.protocol_byte, op, filepath, filename
        )

        retries = 0

        while retries < MAX_RETRIES:
            log.debug(f"--- HANDSHAKE intento {retries+1}/{MAX_RETRIES} ---")
            log.debug(
                f"Se envia el bit de protocolo: {self.protocol_byte} del protocolo {self.name}"
            )

            sender_queue.put((pkg, (self.addr, self.port)))
            log.debug(f"Paquete de handshake enviado")

            try:
                _, pkg = in_queue.get(timeout=TIMEOUT_HANDSHAKE)
                log.debug(f"Paquete de handshake recibido")
                if packageLib.is_ack_handshake_packet(pkg):
                    log.debug(f"EXITOSO\n")
                    return
                else:
                    log.debug(f"FALLIDO, paquete recibido no es ACK de handshake\n")
                    retries += 1

            except queue.Empty:
                log.debug(f"Timeout esperando ACK de handshake, reintentando...\n")
                retries += 1
        log.debug(f"FALLIDO, se agotaron los intentos")
