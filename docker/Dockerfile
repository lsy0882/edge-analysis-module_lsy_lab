FROM sogangmm/tensorrt:20.08-py3-opencv411

RUN DEBIAN_FRONTEND="noninteractive" apt-get -y install tzdata
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes #prohibit-password/' /etc/ssh/sshd_config

WORKDIR /workspace
ADD .. .
ENV PYTHONPATH $PYTHONPATH:/workspace

RUN chmod -R a+w /workspace

EXPOSE 8000
