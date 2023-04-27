FROM ubuntu:20.04

ENV CPLEX_INSTALLER ILOG_COS_20.10_LINUX_X86_64.bin
ENV CPLEX_ROOT /opt/ibm/ILOG/CPLEX_Studio201
ENV TZ=Europe/Zurich
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install dependencies.
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        default-jre     \
        libgmp3-dev     \
        python3         \
        python3-distutils \
        unzip        && \
    rm -rf /var/lib/apt/lists/*

# Install CPLEX.
WORKDIR /third-party/cplex
ADD $CPLEX_INSTALLER .
RUN ./$CPLEX_INSTALLER -DLICENSE_ACCEPTED=TRUE -i silent
RUN python3 $CPLEX_ROOT/python/setup.py install
RUN rm -r $CPLEX_INSTALLER $CPLEX_ROOT
RUN apt-get purge -y default-jre && apt -y autoremove


WORKDIR /workspace/
ADD check-unsolvability.py .
ADD parse.py .
ADD satisfiable.py .
ADD search.py .

RUN groupadd -r user && useradd -r -g user user
USER user

ENTRYPOINT ["/workspace/check-unsolvability.py"]
