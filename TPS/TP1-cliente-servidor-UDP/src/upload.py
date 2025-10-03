from lib.common import args_parser
from lib.client.uploader import Uploader
from lib.common.selective_repeat_protocol import SelectiveRepeat
from lib.common.stop_n_wait_protocol import StopAndWait


def main():
    args = args_parser.parse_upload_arguments(
        description="Subir un archivo al servidor"
    )

    try:
        if args.protocol == SelectiveRepeat.ARG_NAME:
            protocol = SelectiveRepeat(args.host, args.port, args.verbose, args.quiet)
        else:
            protocol = StopAndWait(args.host, args.port, args.verbose, args.quiet)

        uploader = Uploader(protocol, args.verbose, args.quiet)
        uploader.run(args.filepath, args.filename)
    except Exception as e:
        print(f"Error al subir el archivo: {e}")
    except KeyboardInterrupt:
        print("Transferencia interrumpida por el usuario")
        return


if __name__ == "__main__":
    main()
