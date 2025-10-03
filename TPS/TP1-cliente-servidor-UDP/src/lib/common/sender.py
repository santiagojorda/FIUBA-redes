import queue
import threading
from lib.common.log import Log

SENDER_QUEUE_TIMEOUT = 1.0


class Sender(threading.Thread):

    def __init__(self, sock, sender_queue, verbose, quiet):
        threading.Thread.__init__(self)
        self.sock = sock
        self.queue = sender_queue
        self.running = True
        self.log = Log(f"SENDER:", verbose, quiet)

    def run(self):
        self.log.debug("Hilo corriendo")

        while self.running:
            try:
                package, destination_address = self.queue.get(
                    timeout=SENDER_QUEUE_TIMEOUT
                )

                if not self.running:
                    self.queue.task_done()
                    break

                self.sock.sendto(package, destination_address)
                self.queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                self.log.error(f"Error inesperado en Sender: {e}")
                if not self.running:
                    break
                self.queue.task_done()
                continue

    def stop(self):
        self.log.debug("Hilo cerrado")
        self.running = False
