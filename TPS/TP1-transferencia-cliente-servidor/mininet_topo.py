#!/usr/bin/env python3

import os
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node, OVSController
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.cli import CLI
import argparse


class SingleSwitchTopo(Topo):
    "Simple topology with one switch and two hosts"

    def build(self):
        # Add hosts
        client = self.addHost("h1")
        server = self.addHost("h2")

        # Add switch
        s1 = self.addSwitch("s1")

        # Add links with specified loss rate for the client->server path
        self.addLink(client, s1, cls=TCLink, loss=10)  # 10% pérdida de paquetes
        self.addLink(server, s1, cls=TCLink)


def runNetworkTest(source_dir):
    # Create topology
    topo = SingleSwitchTopo()

    # Create and start network with OVS controller
    net = Mininet(topo=topo, link=TCLink, controller=OVSController)
    net.start()

    # Preparar directorio compartido
    print("\n*** Configurando directorios compartidos...")

    # Definir directorios
    shared_dir = "/tmp/tp1_shared"
    project_dir = "/TP1-Redes-Grupo5"

    os.system(f"mkdir -p {shared_dir}")
    os.system(f"cp -r {source_dir}/* {shared_dir}/")

    for host in net.hosts:
        host.cmd(f"mkdir -p {project_dir}")
        host.cmd(f"mount --bind {shared_dir} {project_dir}")
        print(f"Montado directorio compartido en {host.name}")

    print(
        "\nUsage: para acceder a los archivos del proyecto, usa el directorio /TP1-Redes-Grupo5"
    )
    print("Ejemplo: h1 cd /TP1-Redes-Grupo5 && python src/upload.py ...")

    print("\nDumping host connections")
    dumpNodeConnections(net.hosts)

    print("\nTesting network connectivity")
    net.pingAll()

    # Interactive CLI
    CLI(net)

    # Cleanup
    for host in net.hosts:
        host.cmd(f"umount {project_dir}")

    net.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mininet topología para TP1-Redes")
    parser.add_argument(
        "--source-dir",
        type=str,
        default="/home/mosandroni/mac_desktop/Facultad/TP1-Redes-Grupo5",
        help="Directorio origen a copiar en el directorio compartido",
    )
    args = parser.parse_args()

    setLogLevel("info")

    runNetworkTest(args.source_dir)
