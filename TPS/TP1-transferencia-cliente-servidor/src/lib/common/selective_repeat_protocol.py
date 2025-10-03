from lib.common import package as packageLib
import os
import time
import queue
from lib.common.protocol import Protocol

WINDOW_SIZE = 120
MAX_ACKS_TO_WAIT = 10
TIMEOUT_DURATION = 0.05  # 50 ms

ESTIMATED_RTT = 0.05  # 50 ms
DEV_RTT = 0.025  # 25 ms
RTO = 0.2  # 200 ms inicial

MAX_RETRIES = 10

ALPHA = 0.125
BETA = 0.25


class SelectiveRepeat(Protocol):
    NAME = "Selective Repeat"
    ARG_NAME = "selective-repeat"
    PROTOCOL_BYTE = b"\x01"

    def __init__(self, host, port, verbose, quiet):
        super().__init__(
            self.PROTOCOL_BYTE, self.NAME, self.ARG_NAME, host, port, verbose, quiet
        )

        self.running = False
        self.sequence_numbers = {}
        self.acked_packets = set()
        self.next_seq_num = 0
        self.base = 0
        self.timers = {}
        self.retries = {}
        self.estimated_rtt = ESTIMATED_RTT
        self.dev_rtt = DEV_RTT
        self.rto = RTO

    def send_file(
        self, filepath, filename, destination_address, in_queue, sender_queue
    ):

        try:
            chunks = self._read_file_chunks(
                filepath, filename, destination_address, sender_queue
            )
            total_chunks = len(chunks)

            while self.base < total_chunks:
                self._send_window_packets(chunks, destination_address, sender_queue)

                self._wait_for_acks(in_queue)

                self._check_timeouts(chunks, destination_address, sender_queue)

            self.log.print(f"Transferencia completada del archivo {filename}")
        except Exception as e:
            return

        # Enviar FIN solo después de confirmar todos los paquetes
        fin_packet = packageLib.create_fin_packet()
        self._send(fin_packet, destination_address, sender_queue)
        self.log.debug("FIN enviado")

    def receive_file(
        self, filepath, filename, destination_address, in_queue, sender_queue
    ):
        """Método unificado para recibir archivos usando Selective Repeat."""
        first_package = True
        while True:
            try:

                # El formato depende de quién llama:
                # - Cliente: (client_addr, data)
                # - Servidor: data (solo el paquete crudo)
                client_addr, queue_item = in_queue.get(timeout=TIMEOUT_DURATION)

                if isinstance(queue_item, tuple) and len(queue_item) == 2:
                    # Caso cliente: (client_addr, data)
                    client_addr, data = queue_item
                    if packageLib.is_exit_package(data):
                        self.log.print(f"Finalizacion de envio del archivo {filename}")

                        if first_package:
                            self.log.print(f"Archivo {filename} no encontrado")
                    break

                else:
                    # Caso servidor: solo data
                    data = queue_item
                    client_addr = destination_address
                    if packageLib.is_exit_package(data):
                        self.log.debug(f"Finalizacion de envio del archivo {filename}")

                        if first_package:
                            self.log.print(f"Archivo {filename} no encontrado")
                        break
                first_package = False

                parsed = packageLib.parse_packet(data)
                if not parsed:
                    continue

                seq, _ack, _length, _flags, _checksum, payload = parsed

                self.log.debug(
                    f"Procesando: chunk seq={seq} | payload: {len(payload)} bytes"
                )

                last_ack = self._receive_file_chunk(seq, payload, filepath, filename)

                if last_ack is not None and sender_queue is not None:
                    ack_package = packageLib.create_ack_packet(last_ack)
                    sender_queue.put((ack_package, client_addr))
                    self.log.debug(f"ACK enviado para seq={last_ack}")

            except queue.Empty:
                continue
            except Exception as e:
                self.log.debug(f"Error procesando paquete: {e}")
                break

    def _send(self, package, addr, sender_queue):
        sender_queue.put((package, addr))

    def _send_window_packets(self, chunks, destination_address, sender_queue):
        while self.next_seq_num < self.base + WINDOW_SIZE and self.next_seq_num < len(
            chunks
        ):
            chunk_data = chunks[self.next_seq_num]
            packet = packageLib.create_data_packet(self.next_seq_num, chunk_data)
            self._send(packet, destination_address, sender_queue)
            self.timers[self.next_seq_num] = time.time()

            if self.verbose:
                self.log.debug(
                    f"Paquete enviado: seq:{self.next_seq_num}/{len(chunks)} | size: {len(chunk_data)} bytes"
                )

            self.next_seq_num += 1

    def _wait_for_acks(self, in_queue):
        deadline = time.time() + (self.rto * 0.5)
        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                break
            try:
                _addr, data = in_queue.get(timeout=remaining)
            except queue.Empty:
                break
            except Exception as e:
                self.log.debug(f"Error procesando ACK: {e}")

            pkg = packageLib.parse_packet(data)
            if not pkg:
                continue

            ack = packageLib.get_ack(pkg)
            flags = packageLib.get_flags(pkg)

            if flags == packageLib.ACK_FLAG:
                if ack in self.timers:  # calcular sampleRTT
                    sample = time.time() - self.timers[ack]
                    self._update_rto(sample)
                    del self.timers[ack]

                self.acked_packets.add(ack)
                if self.verbose:
                    self.log.debug(f"Recibido ACK para seq:{ack}")

                # Deslizar ventana
                while self.base in self.acked_packets:
                    self.acked_packets.remove(self.base)
                    self.base += 1

    def _receive_file_chunk(self, seq, payload, dest_dir, filename):
        if not hasattr(self, "received_buffer"):
            self.received_buffer = {}
            self.next_expected_seq = 0
            self.file_path = None

        if self.file_path is None:
            storage_dir = os.path.join(os.getcwd(), dest_dir)
            os.makedirs(storage_dir, exist_ok=True)
            self.file_path = os.path.join(storage_dir, filename)
            # Eliminar archivo existente
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
                self.log.debug(f"Archivo existente eliminado: {self.file_path}")
        if seq not in self.received_buffer:
            self.received_buffer[seq] = payload
            self.log.debug(f"Recibo paquete nuevo: seq: {seq} | guardado en buffer")
        else:
            self.log.debug(f"Recibo paquete duplicado: seq: {seq}")

        while self.next_expected_seq in self.received_buffer:
            chunk_to_write = self.received_buffer.pop(self.next_expected_seq)
            with open(self.file_path, "ab") as f:
                data_to_write = (
                    chunk_to_write
                    if isinstance(chunk_to_write, bytes)
                    else chunk_to_write.encode("latin1")
                )
                f.write(data_to_write)
            self.log.debug(
                f"Escribiendo chunk seq={self.next_expected_seq} al archivo (tamanio: {len(chunk_to_write)} bytes)"
            )
            self.next_expected_seq += 1

        # Devolver el ACK (seq) para que el handler lo encole
        return seq

    def _check_timeouts(self, chunks, destination_address, sender_queue):
        current_time = time.time()
        timeouts_queue = [
            (self.timers[seq_num], seq_num)
            for seq_num in range(self.base, min(self.next_seq_num, len(chunks)))
            if seq_num not in self.acked_packets and seq_num in self.timers
        ]

        timeouts_queue.sort()

        for timeout_time, seq_num in timeouts_queue:

            if seq_num not in self.retries:
                self.retries[seq_num] = 0

            if current_time - timeout_time > self.rto:
                if self.retries[seq_num] >= MAX_RETRIES:
                    raise Exception(
                        f"Se supero el maximo de reintentos para seq: {seq_num}"
                    )
                chunk_data = chunks[seq_num]
                packet = packageLib.create_data_packet(seq_num, chunk_data)
                self._send(packet, destination_address, sender_queue)
                self.timers[seq_num] = current_time
                self.retries[seq_num] += 1

                if self.verbose:
                    self.log.debug(
                        f"Timeout (RTO={self.rto:.3f}s) - Retransmitiendo paquete seq:{seq_num}/{len(chunks)}, intento {self.retries[seq_num]}/{MAX_RETRIES}"
                    )

            else:
                break

    def _update_rto(self, sample):
        alpha, beta = ALPHA, BETA
        self.estimated_rtt = (1 - alpha) * self.estimated_rtt + alpha * sample
        self.dev_rtt = (1 - beta) * self.dev_rtt + beta * abs(
            sample - self.estimated_rtt
        )
        # clamp para evitar valores absurdos
        self.rto = max(0.05, min(1.0, self.estimated_rtt + 4 * self.dev_rtt))
        if self.verbose:
            self.log.debug(
                f"Nuevo RTO adaptativo: {self.rto:.3f}s (RTT={self.estimated_rtt:.3f}s)"
            )
