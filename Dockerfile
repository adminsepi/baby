FROM openjdk:21-jdk-slim

# نصب پیش‌نیازها
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    wget \
    unzip \
    curl \
    bash

# نصب Android SDK و ابزارها
ENV ANDROID_SDK_ROOT=/opt/android-sdk
RUN mkdir -p ${ANDROID_SDK_ROOT} && \
    wget -q https://dl.google.com/android/repository/commandlinetools-linux-9477386_latest.zip -O /tmp/cmdline-tools.zip && \
    unzip -q /tmp/cmdline-tools.zip -d ${ANDROID_SDK_ROOT}/cmdline-tools && \
    mv ${ANDROID_SDK_ROOT}/cmdline-tools/cmdline-tools ${ANDROID_SDK_ROOT}/cmdline-tools/latest

# نصب build-tools و platform-tools
ENV PATH=${PATH}:${ANDROID_SDK_ROOT}/cmdline-tools/latest/bin:${ANDROID_SDK_ROOT}/build-tools/34.0.0:${ANDROID_SDK_ROOT}/platform-tools
RUN yes | ${ANDROID_SDK_ROOT}/cmdline-tools/latest/bin/sdkmanager --sdk_root=${ANDROID_SDK_ROOT} "build-tools;34.0.0" "platform-tools" && \
    echo "Verifying tools..." && \
    ls -la ${ANDROID_SDK_ROOT}/build-tools/34.0.0/ && \
    ls -la ${ANDROID_SDK_ROOT}/platform-tools/ && \
    which zipalign && \
    zipalign --version && \
    which apksigner && \
    apksigner --version

# نصب Python و وابستگی‌ها
RUN pip3 install --no-cache-dir flask requests gunicorn werkzeug

# تنظیم کارگاه
WORKDIR /app
COPY . .

ENV PORT=5000
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "app:app"]
