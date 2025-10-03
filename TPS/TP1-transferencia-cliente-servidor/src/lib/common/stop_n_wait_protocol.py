from lib.common.protocol import Protocol
from lib.common import package as packageLib
import os, queue

TIMEOUT = 0.05
MAX_RETRIES = 10


class StopAndWait(Protocol):
    NAME = "Stop & wait"
    ARG_NAME = "stop-n-wait"
    PROTOCOL_BYTE = b"\x00"

    def __init__(self, host, port, verbose, quiet):
        super().__init__(
            self.PROTOCOL_BYTE, self.NAME, self.ARG_NAME, host, port, verbose, quiet
        )

        self.base = 0
        self.expected_seq = 0
        self.last_ack = None

    def send_file(
        self, filepath, filename, destination_address, in_queue, sender_queue
    ):
        """funcion que se encarga de enviar un archivo con stop and wait
        si es el cliente, usa el parametro socket, si es el servidor usa server_queues y in_queue
        """
        seq_num = 0
        chunk_num = 0

        try:
            chunks = self._read_file_chunks(
                filepath, filename, destination_address, sender_queue
            )
            total_chunks = len(chunks)
        except Exception as e:
            return

        for chunk_num, chunk in enumerate(chunks):
            self.log.debug(
                f"Paquete enviado seq: {seq_num} | chunk {chunk_num}/{total_chunks} | size: {len(chunk)} bytes"
            )
            packet = packageLib.create_data_packet(seq_num, chunk)
            retries = 0

            while retries < MAX_RETRIES:
                self._send(packet, destination_address, sender_queue)
                ack_received = self._wait_ack(seq_num, in_queue)

                if not ack_received:
                    retries += 1
                    self.log.debug(
                        f"Reintentando envio del paquete: seq: {seq_num} | intento: {retries}"
                    )
                else:
                    break
            if retries == MAX_RETRIES:
                self.log.debug(f"Timeout al enviar paquete seq: {seq_num}")
                raise Exception(f"Timeout al enviar paquete seq: {seq_num}")

            seq_num = 1 - seq_num

        fin_packet = packageLib.create_fin_packet()
        self._send(fin_packet, destination_address, sender_queue)
        self.log.debug("FIN enviado")
        self.log.print(f"Transferencia completada del archivo {filename}")

    def _wait_ack(self, seq_num, in_queue):
        """Espera su ACK correspondiente"""
        self.log.debug(f"Esperando ACK para seq: {seq_num}")
        try:
            _addr, data = in_queue.get(timeout=TIMEOUT)
            pkg = packageLib.parse_packet(data)
            if pkg:
                ack = packageLib.get_ack(pkg)
                flags = packageLib.get_flags(pkg)
                if flags == packageLib.ACK_FLAG and ack == seq_num:
                    self.log.debug(f"ACK recibido seq: {ack}")
                    return True
        except queue.Empty:
            self.log.debug(f"Timeout esperando ACK seq: {seq_num}, reintentando...")
            return False
        except Exception as e:
            self.log.debug(f"Error esperando ACK: {e}")
        return False

    def receive_file(
        self, filepath, filename, _destination_address, in_queue, sender_queue
    ):
        """Método unificado para recibir paquetes."""

        # si le llega un paquete de fin al principio es por que no existe

        first_package = True
        while True:
            try:
                client_addr, queue_item = in_queue.get(timeout=TIMEOUT)

                if packageLib.is_exit_package(queue_item):
                    self.log.debug("FIN recibido, finalizando recepcion.")

                    if first_package:
                        self.log.print(f"Archivo {filename} no encontrado")

                    break

                first_package = False

                parsed = packageLib.parse_packet(queue_item)
                if not parsed:
                    continue

                seq, _ack, _length, _flags, _checksum, payload = parsed
                self.log.debug(
                    f"Procesando chunk: seq: {seq} | payload: {len(payload)} bytes"
                )

                last_ack = self._receive_file_chunk(seq, payload, filepath, filename)

                if last_ack is not None and sender_queue is not None:
                    ack_package = packageLib.create_ack_packet(last_ack)
                    sender_queue.put((ack_package, client_addr))
                    self.log.debug(f"ACK enviado seq: {last_ack}")

            except queue.Empty:
                continue
            except Exception as e:
                self.log.debug(f"Error procesando paquete: {e}")
                break

    def _receive_file_chunk(self, seq, payload, dest_dir, filename):
        """Función que maneja un paquete de datos recibido. Devuelve el último ACK
        recibido"""
        if seq == self.expected_seq:
            storage_dir = os.path.join(os.getcwd(), dest_dir)
            os.makedirs(storage_dir, exist_ok=True)

            file_path = os.path.join(storage_dir, filename)

            if self.last_ack is None and self.expected_seq == 0 and seq == 0:
                try:
                    os.remove(file_path)
                    self.log.debug(f"Archivo existente eliminado: {file_path}")
                except FileNotFoundError:
                    pass

            with open(file_path, "ab") as f:
                data_to_write = (
                    payload if isinstance(payload, bytes) else payload.encode("utf-8")
                )
                f.write(data_to_write)

            self.log.debug(f"Guardado chunk: seq:{seq} | size: {len(payload)} bytes")
            self.last_ack = seq
            self.expected_seq = 1 - self.expected_seq
        else:
            self.log.debug(f"Duplicado recibido seq:{seq} | reenvio ultimo ACK")

        return self.last_ack
