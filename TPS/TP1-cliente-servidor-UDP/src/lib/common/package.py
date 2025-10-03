import struct
from lib.common.common import to_bytes

# FLAGS
DATA_FLAG = 0x01  # Flag para paquetes de datos
ACK_FLAG = 0x02  # Flag para paquetes de ACK
HAND_SHAKE_FLAG = 0x04  # Flag para paquetes de FIN
FIN_FLAG = 0x08  # Flag para paquetes de FIN

HEADER_FORMAT = "!HHHBH"  # seq(2), ack(2), len(2), flags(1), cksum(2)

# POSITIONS
POS_SEQ = 0
POS_ACK = 1
POS_LEN = 2
POS_FLAGS = 3
POS_CKSUM = 4
POS_PAYLOAD = 5


def _get_header_size():
    return struct.calcsize(HEADER_FORMAT)


def _create_header(seq, ack, length, flags):
    return struct.pack(HEADER_FORMAT, seq, ack, length, flags, 0)


def _create_packet(seq, ack, flags, payload: bytes = b""):
    length = len(payload)
    header = _create_header(seq, ack, length, flags)
    return header + payload


def _get_header_data(packet):
    if not packet or len(packet) < _get_header_size():
        return None

    header = packet[: _get_header_size()]
    try:
        return struct.unpack(HEADER_FORMAT, header)
    except struct.error:
        print(f"Error al desempaquetar header: {packet}")
        return None


def _check_flag(packet, flag):
    header_data = _get_header_data(packet)
    if header_data is None:
        return False
    flags = header_data[POS_FLAGS]
    return flags == flag


def _check_flag_combination(packet, expected_flags):
    header_data = _get_header_data(packet)
    if header_data is None:
        return False
    flags = header_data[POS_FLAGS]
    return (flags & expected_flags) == expected_flags


def get_payload(parsed_packet):
    return parsed_packet[POS_PAYLOAD]


def get_seq(parsed_packet):
    return parsed_packet[POS_SEQ]


def get_ack(parsed_packet):
    return parsed_packet[POS_ACK]


def get_flags(parsed_packet):
    return parsed_packet[POS_FLAGS]


def is_exit_package(package):
    return _check_flag(package, FIN_FLAG)


def parse_packet(data):
    header_data = _get_header_data(data)
    if header_data is None:
        return None
    seq, ack, length, flags, checksum = header_data
    header_size = _get_header_size()
    payload = data[header_size : header_size + length]
    return (seq, ack, length, flags, checksum, payload)


def parse_handshake_payload(payload: bytes):
    if not payload or len(payload) < 2:
        return None
    protocol_byte = payload[0:1]
    op = payload[1]
    rest = payload[2:]
    parts = rest.split(b"\0")
    file_path = parts[0].decode("utf-8", errors="ignore") if len(parts) >= 1 else ""
    file_name = parts[1].decode("utf-8", errors="ignore") if len(parts) >= 2 else ""
    return protocol_byte, op, file_path, file_name


def create_data_packet(seq, payload):
    return _create_packet(seq, 0, DATA_FLAG, payload)


def create_ack_packet(ack):
    return _create_packet(0, ack, ACK_FLAG)


def create_handshake_packet(
    protocol_byte, op, file_path, file_name="file.txt", extra_payload: bytes = b""
):
    payload = (
        to_bytes(protocol_byte)
        + to_bytes(op)
        + file_path.encode("utf-8")
        + b"\0"
        + file_name.encode("utf-8")
        + b"\0"
        + (extra_payload or b"")
    )
    return _create_packet(0, 0, HAND_SHAKE_FLAG, payload)


def create_ack_handshake_packet():
    return _create_packet(0, 0, ACK_FLAG | HAND_SHAKE_FLAG)


def is_handshake_packet(packet):
    return _check_flag_combination(packet, HAND_SHAKE_FLAG)


def is_ack_handshake_packet(packet):
    return _check_flag_combination(packet, ACK_FLAG | HAND_SHAKE_FLAG)


def create_fin_packet():
    return _create_packet(0, 0, FIN_FLAG)
