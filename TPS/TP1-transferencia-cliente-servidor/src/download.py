from lib.common import args_parser
from lib.client.downloader import Downloader
from lib.common.selective_repeat_protocol import SelectiveRepeat
from lib.common.stop_n_wait_protocol import StopAndWait


def main():
    args = args_parser.parse_download_arguments(
        description="Descargar un archivo desde el servidor"
    )

    try:
        if args.protocol == SelectiveRepeat.ARG_NAME:
            protocol = SelectiveRepeat(args.host, args.port, args.verbose, args.quiet)
        else:
            protocol = StopAndWait(args.host, args.port, args.verbose, args.quiet)

        downloader = Downloader(protocol, args.verbose, args.quiet)
        downloader.run(args.filepath, args.filename)
    except Exception as e:
        print(f"Error al subir el archivo: {e}")
    except KeyboardInterrupt:
        print("Transferencia interrumpida por el usuario")
        return


if __name__ == "__main__":
    main()
