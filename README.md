# FICS


# Download & configure FICS

1. Clone the repository
  - For example: mkdir /home/mansour/code
  - cd /home/mansour/code
  - ```git clone --recurse-submodules https://github.com/RiS3-Lab/FICS-.git```
  - cd FICS
2. ```sh install.sh```
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
  - For example: ```sh scripts/get_inconsistencies_real_programs_NN_G2v.sh libtiff-19f6b70 p ns```
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

# Citation

If your found FICS useful for your research, please cite the following paper:

```Latex
@inproceedings{fics,
 abstract = {
Probabilistic classification has shown success in detecting known types of software bugs. However, the works following this approach tend to require a large amount of specimens to train their models. We present a new machine learning-based bug detection technique that does not require any external code or samples for training. Instead, our technique learns from the very codebase on which the bug detection is performed, and therefore, obviates the need for the cumbersome task of gathering and cleansing training samples (e.g., buggy code of certain kinds). The key idea behind our technique is a novel two-step clustering process applied on a given codebase. This clustering process identifies code snippets in a project that are functionally-similar yet appear in inconsistent forms. Such inconsistencies are found to cause a wide range of bugs, anything from missing checks to unsafe type conversions. Unlike previous works, our technique is generic and not specific to one type of inconsistency or bug. We prototyped our technique and evaluated it using 5 popular open source software, including QEMU and OpenSSL. With a minimal amount of manual analysis on the inconsistencies detected by our tool, we discovered 22 new unique bugs, despite the fact that many of these programs are constantly undergoing bug scans and new bugs in them are believed to be rare.
},
 author = {Ahmadi, Mansour and Mirzazade farkhani, Reza and  Williams, Ryan and Lu, Long},
 booktitle = {Proceedings of the 30th USENIX Security Symposium},
 month = {August},
 series = {USENIX Security'21},
 title = {Finding Bugs Using Your Own Code: Detecting Functionally-similar yet Inconsistent Code},
 year = {2021}
 ```
}
