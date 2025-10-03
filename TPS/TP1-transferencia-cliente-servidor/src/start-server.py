import os
from lib.common import args_parser
from lib.server.server import Server


def main():
    try:
        args = args_parser.parse_server_arguments(description="Iniciar el servidor")

        storage_path = args.DIRPATH
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)

        server = Server(args.host, args.port, storage_path, args.verbose, args.quiet)
        server.run()
    except Exception as e:
        print(f"Error al subir el archivo: {e}")
    except KeyboardInterrupt:
        print("Transferencia interrumpida por el usuario")
        return


if __name__ == "__main__":
    main()
