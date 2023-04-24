FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends git curl ca-certificates default-jre
## example-solver-specific: install scala runtime
RUN curl -fL https://github.com/coursier/coursier/releases/latest/download/cs-x86_64-pc-linux.gz | gzip -d > cs && \
    chmod +x cs && ./cs install scala:2.12.17 && \
    rm cs

# Set up your solver
RUN git clone --depth 1 https://github.com/core-challenge/util-example-solver.git /util-example-solver

# Set environment variables if needed
ENV PATH $PATH:/root/.local/share/coursier/bin
ENV JAVA_OPTS -Xms16g -Xmx16g

# specify the solver command
ENTRYPOINT ["scala", "-cp", "/util-example-solver/lib/scop.jar:/util-example-solver/target/scala-2.12/coresolver_2.12-1.3.5.jar", "fun.scop.app.isr.IsrSolver"]
