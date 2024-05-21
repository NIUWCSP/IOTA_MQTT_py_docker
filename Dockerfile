# 使用官方的Python镜像作为基础镜像
FROM python:3.9-slim

# 更新和安装必要的工具和依赖项
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y clang libusb-1.0-0-dev libudev-dev curl git bash \
    autoconf automake libtool make g++ pkg-config

# 安装Rust和Cargo
RUN curl https://sh.rustup.rs -sSf | bash -s -- -y

# 确保Rust和Cargo在当前环境可用
ENV PATH="/root/.cargo/bin:${PATH}"

# 构建iota-sdk
WORKDIR /usr/src
RUN git clone https://github.com/iotaledger/iota-sdk.git && \
    cd iota-sdk && \
    cargo build --release

# 设置Python虚拟环境
RUN python3 -m venv /usr/src/iota_sdk_venv

# 激活虚拟环境并安装必要的Python库
RUN /usr/src/iota_sdk_venv/bin/pip install --upgrade pip

# 复制IOT2Tangle_MQTT Gateway代码到容器中
COPY . /usr/src/IOTA_MQTT_py

# 安装IOT2Tangle_MQTT Gateway依赖项
WORKDIR /usr/src/IOTA_MQTT_py
RUN /bin/bash -c "source /usr/src/iota_sdk_venv/bin/activate && pip install -r requirements_docker.txt"

# 设置工作目录
WORKDIR /usr/src/IOTA_MQTT_py

# 启动容器时执行的命令
CMD ["/bin/bash", "-c", "source /usr/src/iota_sdk_venv/bin/activate && python iota.py"]