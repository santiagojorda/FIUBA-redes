from lib.common.selective_repeat_protocol import SelectiveRepeat
from lib.common.stop_n_wait_protocol import StopAndWait
from lib.common.common import to_bytes


class ProtocolFactory:
    @staticmethod
    def create_protocol(protocol_byte, addr, port, verbose=False, quiet=False):
        protocol_byte = to_bytes(protocol_byte)

        if protocol_byte == SelectiveRepeat.PROTOCOL_BYTE:
            return SelectiveRepeat(host=addr, port=port, verbose=verbose, quiet=quiet)
        elif protocol_byte == StopAndWait.PROTOCOL_BYTE:
            return StopAndWait(host=addr, port=port, verbose=verbose, quiet=quiet)
        else:
            raise ValueError(f"Protocolo no reconocido: {protocol_byte}")
