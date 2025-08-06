FROM openjdk:21-jdk-slim

# نصب پیش‌نیازها
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    wget \
    unzip \
    bash

# دانلود و نصب Android SDK Tools فقط برای apksigner
ENV ANDROID_HOME=/opt/android-sdk
RUN mkdir -p ${ANDROID_HOME} && \
    wget -q https://dl.google.com/android/repository/sdk-tools-linux-4333796.zip -O /tmp/sdk-tools.zip && \
    unzip -q /tmp/sdk-tools.zip -d ${ANDROID_HOME} && \
    echo y | ${ANDROID_HOME}/tools/bin/sdkmanager "build-tools;34.0.0" && \
    echo "Verifying apksigner..." && \
    APK_SIGNER_PATH=$(find ${ANDROID_HOME}/build-tools/ -name apksigner | head -n 1) && \
    if [ -z "$APK_SIGNER_PATH" ]; then echo "Error: apksigner not found!" && exit 1; else echo "Found apksigner at: ${APK_SIGNER_PATH}" && ${APK_SIGNER_PATH} --version; fi

# نصب Python و وابستگی‌ها
RUN pip3 install --no-cache-dir flask requests gunicorn werkzeug

# تنظیم کارگاه
WORKDIR /app
COPY . .

ENV PORT=5000
ENV APK_SIGNER_PATH=${APK_SIGNER_PATH}
CMD ["sh", "-c", "echo 'Using APK_SIGNER_PATH at runtime: ${APK_SIGNER_PATH}' && gunicorn --bind 0.0.0.0:${PORT} app:app"]
