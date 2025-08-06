FROM androguard/android-sdk:latest

# نصب پیش‌نیازها
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    bash

# تنظیم محیط Android SDK
ENV ANDROID_SDK_ROOT=/opt/android-sdk
ENV PATH=${PATH}:${ANDROID_SDK_ROOT}/cmdline-tools/latest/bin:${ANDROID_SDK_ROOT}/build-tools/34.0.0:${ANDROID_SDK_ROOT}/platform-tools

# پیدا کردن مسیر zipalign
RUN echo "Verifying tools..." && \
    ZIPALIGN_PATH=$(find ${ANDROID_SDK_ROOT}/build-tools/ -name zipalign | head -n 1) && \
    if [ -z "$ZIPALIGN_PATH" ]; then echo "Error: zipalign not found!" && exit 1; else echo "Found zipalign at: ${ZIPALIGN_PATH}" && ls -la ${ZIPALIGN_PATH} && ${ZIPALIGN_PATH} --version; fi && \
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
