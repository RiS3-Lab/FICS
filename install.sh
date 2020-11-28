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
