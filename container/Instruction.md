# Compiling the Docker image

To build the Docker image with CPLEX support, you need to obtain a license for
CPLEX. IBM offers [free academic licenses](https://ibm.com/academic).

Afterwards, please download the CPLEX 22.11 installer for Linux and place it in
the same directory as the Dockerfile. It should be called
cplex_studio2211.linux_x86_64.bin.

Then call `docker build .` as usual.

Without CPLEX, the build will fall back to use the open source solver SCIP, but
this will have worse performance.