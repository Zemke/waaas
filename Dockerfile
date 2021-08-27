FROM wa:latest

# Define custom function directory
ENV FUNCTION_DIR="/function"

RUN apt-get update \
  && apt-get install -y python3.8 python3.8-dev python3.8-distutils python3.8-venv python3-pip \
  && ln -s /usr/bin/python3.8 /usr/local/bin/python \
  && python -m pip install pip \
  && python -m pip install --upgrade setuptools \
  && apt-get install -y autoconf g++ make cmake unzip libcurl4-openssl-dev libtool libtool-bin \
  && python -m pip install boto3 image \
  && mkdir -p ${FUNCTION_DIR} \
  && python -m pip install --target ${FUNCTION_DIR} awslambdaric

COPY lambda/* ${FUNCTION_DIR}
COPY lambda/entry_script.sh /entry_script.sh

ADD lambda/aws-lambda-rie /usr/local/bin/aws-lambda-rie

WORKDIR ${FUNCTION_DIR}

CMD [ "app.handler" ]

ENTRYPOINT [ "/entry_script.sh" ]

