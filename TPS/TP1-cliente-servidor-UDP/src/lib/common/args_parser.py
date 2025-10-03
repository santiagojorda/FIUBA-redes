import argparse
from lib.common import constants
from lib.common.stop_n_wait_protocol import StopAndWait
from lib.common.selective_repeat_protocol import SelectiveRepeat

DEFAULT_FILEPATH_UPLOAD = "./files"
DEFAULT_FILEPATH_DOWNLOAD = "./storage"
DEFAULT_FILENAME = "file.txt"


def _build_parser(description=None):
    return argparse.ArgumentParser(
        description=description or "Missing description.",
        formatter_class=argparse.RawTextHelpFormatter,
    )


def parse_common_arguments(parser):
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Aumentar la verbosidad de la salida.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Disminuir la verbosidad de la salida.",
    )
    parser.add_argument(
        "-H",
        "--host",
        default=constants.HOST,
        help=f"Dirección IP del servidor (default: {constants.HOST})",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=constants.DEFAULT_PORT,
        help=f"Puerto del servidor (default: {constants.DEFAULT_PORT})",
    )


def parse_upload_arguments(description=None):
    parser = _build_parser(description)

    parse_common_arguments(parser)
    parser.add_argument(
        "-s",
        "--src",
        dest="filepath",
        default=DEFAULT_FILEPATH_UPLOAD,
        help=f"source file path (default: {DEFAULT_FILEPATH_UPLOAD})",
    )
    parser.add_argument(
        "-n",
        "--name",
        dest="filename",
        default=DEFAULT_FILENAME,
        help=f"Nombre del archivo (default: {DEFAULT_FILENAME})",
    )
    parser.add_argument(
        "-r",
        "--protocol",
        default=StopAndWait.ARG_NAME,
        choices=[StopAndWait.ARG_NAME, SelectiveRepeat.ARG_NAME],
        help="Protocolo de recuperación de errores (default: stop & wait)",
    )
    parser.add_argument(
        "--simulate-loss",
        action="store_true",
        help="Simula la pérdida de paquetes (10%%)",
    )
    return parser.parse_args()


def parse_server_arguments(description=None):
    parser = _build_parser(description)
    parse_common_arguments(parser)
    parser.add_argument(
        "-s",
        "--DIRPATH",
        default=constants.STORAGE_PATH,
        help=f"storage dir path (default: {constants.STORAGE_PATH})",
    )
    return parser.parse_args()


def parse_download_arguments(description=None):
    parser = _build_parser(description)

    parse_common_arguments(parser)
    parser.add_argument(
        "-d",
        "--dst",
        dest="filepath",
        default=DEFAULT_FILEPATH_DOWNLOAD,
        help=f"source file path (default: {DEFAULT_FILEPATH_DOWNLOAD})",
    )
    parser.add_argument(
        "-n",
        "--name",
        dest="filename",
        default=DEFAULT_FILENAME,
        help=f"Nombre del archivo (default: {DEFAULT_FILENAME})",
    )
    parser.add_argument(
        "-r",
        "--protocol",
        default=StopAndWait.ARG_NAME,
        choices=[StopAndWait.ARG_NAME, SelectiveRepeat.ARG_NAME],
        help="Protocolo de recuperación de errores (default: stop & wait)",
    )
    return parser.parse_args()
