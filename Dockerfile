FROM openjdk:21-jdk-slim

# نصب پیش‌نیازها
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    wget \
    unzip \
    curl \
    bash

# تنظیم محیط Android SDK
ENV ANDROID_SDK_ROOT=/opt/android-sdk
RUN mkdir -p ${ANDROID_SDK_ROOT} && \
    wget -q https://dl.google.com/android/repository/commandlinetools-linux-9477386_latest.zip -O /tmp/cmdline-tools.zip && \
    unzip -q /tmp/cmdline-tools.zip -d ${ANDROID_SDK_ROOT}/cmdline-tools && \
    mv ${ANDROID_SDK_ROOT}/cmdline-tools/cmdline-tools ${ANDROID_SDK_ROOT}/cmdline-tools/latest

# نصب build-tools و platform-tools با چند نسخه
ENV PATH=${PATH}:${ANDROID_SDK_ROOT}/cmdline-tools/latest/bin:${ANDROID_SDK_ROOT}/build-tools/
RUN echo "Installing Android tools..." && \
    for version in 34.0.0 33.0.0 32.0.0; do \
        yes | ${ANDROID_SDK_ROOT}/cmdline-tools/latest/bin/sdkmanager --sdk_root=${ANDROID_SDK_ROOT} "build-tools;${version}" "platform-tools" && \
        ZIPALIGN_PATH=$(find ${ANDROID_SDK_ROOT}/build-tools/ -name zipalign | head -n 1) && \
        if [ -n "$ZIPALIGN_PATH" ]; then echo "Found zipalign at: ${ZIPALIGN_PATH}" && break; fi; \
    done && \
    if [ -z "$ZIPALIGN_PATH" ]; then echo "Error: zipalign not found in any version!" && exit 1; fi && \
    ls -la ${ZIPALIGN_PATH} && \
    ${ZIPALIGN_PATH} --version && \
    which apksigner && \
    apksigner --version

# نصب Python و وابستگی‌ها
RUN pip3 install --no-cache-dir flask requests gunicorn werkzeug

# تنظیم کارگاه
WORKDIR /app
COPY . .

ENV PORT=5000
ENV ZIPALIGN_PATH=${ZIPALIGN_PATH}
CMD ["sh", "-c", "echo 'Using ZIPALIGN_PATH at runtime: ${ZIPALIGN_PATH}' && gunicorn --bind 0.0.0.0:${PORT} app:app"]
