sudo apt-get update
sudo apt-get -y install clang-3.8
sudo apt-get -y install clang-6.0
sudo apt-get -y install llvm-3.8
sudo apt-get -y install llvm-6.0
sudo apt-get -y install bear
sudo apt-get -y install git
sudo apt-get -y install cmake
sudo apt-get -y install libpng-dev libfreetype6-dev
sudo apt-get -y install python-dev graphviz libgraphviz-dev pkg-config
sudo apt-get -y install python-pip
pip install --upgrade pip
pip install --upgrade setuptools
pip install -r requirements.txt
cd dg
cmake -D CMAKE_C_COMPILER="/usr/bin/clang-6.0" -D CMAKE_CXX_COMPILER="/usr/bin/clang++-6.0" .
make
wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/4.4 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.4.list
sudo apt-get update
sudo apt-get install -y mongodb-org=4.4.2 mongodb-org-server=4.4.2 mongodb-org-shell=4.4.2 mongodb-org-mongos=4.4.2 mongodb-org-tools=4.4.2
sudo systemctl start mongod
