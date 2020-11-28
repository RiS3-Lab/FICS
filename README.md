# FICS


# Download & configure FICS

1. Clone the repository
  - For example: mkdir /home/mansour/code
  - cd /home/mansour/code
  - git clone --recurse-submodules repo-url
  - cd FICS
2. sh install.sh
3. create a directory as the root of your data (e.g., source code, bitcodes, graphs, etc.)
  - For example: mkdir /home/mansour/data
  - cd /home/mansour/data
  - create a directory inside and name it 'projects': mkdir projects
  - cd /home/mansour/data/projects
4. Modify settings.py and update DATA_DIR to the root of your data
  - For example: DATA_DIR = '/home/mansour/data'
  
# Prepare target codebase

5. clone the source code a codebase you target:
  - For example: git clone https://gitlab.com/libtiff/libtiff.git libtiff-19f6b70
  - cd libtiff-19f6b70
  - git checkout 19f6b70 .
6. Compile the project with clang-3.8 and get compilation database (FICS just supports clang 3.8 and llvm 3.8)
  - For example: cmake -D CMAKE_C_COMPILER="/usr/bin/clang-3.8" -D CMAKE_CXX_COMPILER="/usr/bin/clang++-3.8" .
  - get compilation database: bear make

# Discover inconsistencies

7. Run FICS on the target codebase:
  - For example: sh scripts/get_inconsistencies_real_programs_NN_G2v.sh libtiff-19f6b70 p ns
  - If you need to run FICS on larger projects like QEMU, change 'ns' to 's'. FICS splits the codebase to submodules
  - *The inconsistencies are saved in mongodb*

# See Inconsistencies!
8. To query the saved inconsistencies, you need to run the following command:
  - ```python __init__.py -a=QI -p=libtiff-19f6b70 -it=check -f```
  - -it can be: check | call | type | store | order | all
  - if you need to disable filtering, just remove -f

# Here is the list of bugs found by FICS

| Bug | Link | 
| ------------- | ------------- |
|  Codebase | OpenSSL  |
| Missing check | [Report/Patch](https://github.com/openssl/openssl/issues/7650) |
| Missing check | [Patch](https://github.com/openssl/openssl/pull/7427)|
| Wrong use of clear_free | [Report/Patch](https://github.com/openssl/openssl/issues/10406)|
| Null dereference | [Report/Patch](https://github.com/openssl/openssl/issues/10404)|
| Null dereference | [Report/Patch](https://github.com/openssl/openssl/issues/10405)|
| Inconsistent Check | [Report/Patch](https://github.com/openssl/openssl/pull/7880)|
| Memory Leak | [Report/Patch](https://github.com/openssl/openssl/issues/10294)|
| Missing clear_free | [Report/Patch](https://github.com/openssl/openssl/issues/7657)|
|  Codebase | QEMU  |
| 2 Missing checks | [Report/Patch](https://patchew.org/QEMU/20200414133052.13712-1-philmd@redhat.com/20200414133052.13712-11-philmd@redhat.com/) |
| Undefined Behaviour  | [Report](https://lists.gnu.org/archive/html/qemu-devel/2020-03/msg05749.html)/[Patch](https://patchwork.kernel.org/patch/11446203/) |
| Uninitialized variable | [Report/Patch](https://lists.gnu.org/archive/html/qemu-trivial/2020-03/msg00239.html) |
|  Codebase | LibTIFF  |
| Missing checks | [Patch](https://gitlab.com/libtiff/libtiff/-/merge_requests/96)
| Mislocated check - Bad casting | [Report/Patch](https://gitlab.com/libtiff/libtiff/-/issues/162)|
| Missing TIFFClose | [Report/Patch](https://gitlab.com/libtiff/libtiff/-/issues/171)
|  Codebase | libredwg  |
| Bad casting (Overflow)  | [Report](https://github.com/LibreDWG/libredwg/issues/174)/[Patch](https://github.com/LibreDWG/libredwg/commit/631bbacb3e18403db1015ef4063c3d19e9c8e11a) | 
| Null dereference  | [Report](https://github.com/LibreDWG/libredwg/issues/172)/[Patch](https://github.com/LibreDWG/libredwg/commit/373c8e4849f2013d7123913bca8edb35ff6bc3d6) | 
| Null dereference  | [Report](https://github.com/LibreDWG/libredwg/issues/173)/[Patch](https://github.com/LibreDWG/libredwg/commit/373c8e4849f2013d7123913bca8edb35ff6bc3d6) | 


