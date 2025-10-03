sudo rm -r logs
sudo mkdir logs
source env/bin/activate
sudo chmod a+w logs/server.log
sudo pkill -f ovs-testcontroller
sudo mn -c
sudo python3 mininet_topo.py --source-dir /home/san/FIUBA/REDES/TP1-Redes-Grupo5

