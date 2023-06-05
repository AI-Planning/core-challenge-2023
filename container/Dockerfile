##################
# Stage 1: Builder
##################

FROM ubuntu:20.04 AS builder

ENV TZ=Europe/Zurich
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN DEBIAN_FRONTEND=noninteractive \
    apt-get update && \
    apt-get -y upgrade && \
    apt-get install -y \
        autoconf \
        bash \
        build-essential \
        ca-certificates \
        cmake \
        curl \
        default-jre     \
        g++ \
        git \
        libgmp3-dev     \
        python3         \
        python3-distutils \
        python3-pip \
        unzip \
        patchelf \
    && rm -rf /var/lib/apt/lists/*

# Build the CPLEX solver if available, otherwise fall back to SCIP.
# We use the file sentinel so the copy works if CPLEX is not present
# (see https://stackoverflow.com/a/46801962).
COPY sentinel cplex_studio2211.linux_x86_64.bin* /
ENV CPLEX_INSTALLER=/cplex_studio2211.linux_x86_64.bin
ENV CPLEX_ROOT=/opt/ibm/ILOG/CPLEX_Studio2211/
RUN if [ -f "$CPLEX_INSTALLER" ]; then \
        chmod u+x $CPLEX_INSTALLER && \
        $CPLEX_INSTALLER -DLICENSE_ACCEPTED=TRUE -i silent && \
        python3 $CPLEX_ROOT/python/setup.py install && \
        rm -r $CPLEX_INSTALLER; \
    else \
        echo "No CPLEX"; \ 
    fi

# Prevent Docker from caching the cloned repo if it changes (https://stackoverflow.com/a/39278224)
ADD https://api.github.com/repos/AI-Planning/core-challenge-2023/git/refs/heads/main version.json
RUN git clone --depth 1 https://github.com/AI-Planning/core-challenge-2023.git /core-challenge-2023

# Build SCIP.
ENV SCIP_INSTALLER=/scip_installer.sh
ENV SCIPOPTDIR=/scip
COPY scip_installer.sh $SCIP_INSTALLER
#curl -fL https://www.scipopt.org/download/release/SCIPOptSuite-8.0.3-Linux-ubuntu.sh > $SCIP_INSTALLER && \
RUN mkdir scip && \
    cd scip && \
    chmod u+x $SCIP_INSTALLER && \
    $SCIP_INSTALLER --skip-licencse --exclude-subdir && \
    rm $SCIP_INSTALLER && \
    pip3 install pyscipopt

# Build Scorpion.
RUN cd /core-challenge-2023/src/scorpion && ./build.py && strip --strip-all builds/release/bin/downward && strip --strip-all builds/release/bin/preprocess-h2

# Build SymK.
RUN cd /core-challenge-2023/src/symk && ./build.py && strip --strip-all builds/release/bin/downward && strip --strip-all builds/release/bin/preprocess


#################
# Stage 2: Runner
#################

FROM ubuntu:20.04 AS runner

RUN DEBIAN_FRONTEND=noninteractive \
    apt-get update && \
    apt-get -y upgrade && \
    apt-get install --no-install-recommends -y \
      python3  \
      python3-pip \
      time \
      libgfortran5 \
      liblapack-dev \
      libtbb-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install cheetah3 psutil natsort==8.3.1

# Copy the relevant files from the previous docker build into this build.
WORKDIR /solvers/scorpion
COPY --from=builder /core-challenge-2023/src/scorpion/fast-downward.py ./
COPY --from=builder /core-challenge-2023/src/scorpion/builds/release/bin/ ./builds/release/bin/
COPY --from=builder /core-challenge-2023/src/scorpion/driver ./driver

WORKDIR /solvers/symk
COPY --from=builder /core-challenge-2023/src/symk/fast-downward.py ./
COPY --from=builder /core-challenge-2023/src/symk/builds/release/bin/ ./builds/release/bin/
COPY --from=builder /core-challenge-2023/src/symk/driver ./driver

WORKDIR /solvers/mip
COPY --from=builder /core-challenge-2023/src/mip .
COPY --from=builder /scip/lib /scip/lib
COPY --from=builder /scip/include /scip/include
COPY --from=builder /usr/local/lib/python3.8/dist-packages/ /usr/local/lib/python3.8/dist-packages/

WORKDIR /solvers/driver
COPY --from=builder /core-challenge-2023/src/driver .


ENTRYPOINT ["/solvers/driver/run.py"]
