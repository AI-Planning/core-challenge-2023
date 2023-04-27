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
        build-essential \
        ca-certificates \
        cmake \
        default-jre     \
        g++ \
        git \
        libgmp3-dev     \
        python3         \
        python3-distutils \
        unzip \
    && rm -rf /var/lib/apt/lists/*

# Build the CPLEX solver if available, otherwise fall back to SCIP.
# We use Dockerfile as a sentinel (see https://stackoverflow.com/a/46801962).
COPY Dockerfile cplex_studio2211.linux_x86_64.bin* .
ENV CPLEX_INSTALLER=/cplex_studio2211.linux_x86_64.bin
ENV CPLEX_ROOT=/opt/ibm/ILOG/CPLEX_Studio221/
RUN if [ -f "$CPLEX_INSTALLER" ]; then \
        chmod u+x $CPLEX_INSTALLER && \
        ./$CPLEX_INSTALLER -DLICENSE_ACCEPTED=TRUE -i silent && \
        python3 $CPLEX_ROOT/python/setup.py install && \
        rm -r $CPLEX_INSTALLER; \
    else \
        echo "No CPLEX"; \ 
    fi

RUN git clone --depth 1 https://github.com/AI-Planning/core-challenge-2023.git /core-challenge-2023

# Build Scorpion.
RUN cd /core-challenge-2023/scorpion && ./build.py && strip --strip-all builds/release/bin/downward

# Build SymK.
RUN cd /core-challenge-2023/symk && ./build.py && strip --strip-all builds/release/bin/downward


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
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install cheetah3

# Copy the relevant files from the previous docker build into this build.
WORKDIR /solvers/scorpion
COPY --from=builder /core-challenge-2023/scorpion/fast-downward.py .
COPY --from=builder /core-challenge-2023/scorpion/builds/release/bin/ ./builds/release/bin/
COPY --from=builder /core-challenge-2023/scorpion/driver ./driver

WORKDIR /solvers/symk
COPY --from=builder /core-challenge-2023/symk/fast-downward.py .
COPY --from=builder /core-challenge-2023/symk/builds/release/bin/ ./builds/release/bin/
COPY --from=builder /core-challenge-2023/symk/driver ./driver

WORKDIR /solvers/mip
COPY --from=builder /core-challenge-2023/mip .
COPY --from=builder /usr/local/lib/python3.8/dist-packages/ /usr/local/lib/python3.8/dist-packages/

WORKDIR /driver
COPY --from=builder /core-challenge-2023/driver .

ENTRYPOINT ["/core-challenge-2023/driver/run.py"]
