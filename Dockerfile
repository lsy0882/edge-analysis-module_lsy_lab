FROM nvcr.io/nvidia/tensorrt:20.08-py3

RUN apt-get update \
    && apt-get -y install libgl1 python3 \
    python3-pip \
    python3-dev \
    git vim openssh-server

RUN DEBIAN_FRONTEND="noninteractive" apt-get -y install tzdata
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes #prohibit-password/' /etc/ssh/sshd_config

WORKDIR /workspace
ADD . .
ENV PYTHONPATH $PYTHONPATH:/workspace

RUN chmod -R a+w /workspace

EXPOSE 8000
