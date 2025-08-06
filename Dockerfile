
FROM androguard/android-sdk:latest

# نصب پیش‌نیازها
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    bash

# تنظیم محیط Android SDK
ENV ANDROID_HOME=/opt/android-sdk
ENV PATH=${PATH}:${ANDROID_HOME}/cmdline-tools/latest/bin:${ANDROID_HOME}/platform-tools

# پیدا کردن مسیر apksigner با جستجوی کامل
RUN echo "Verifying tools..." && \
    APK_SIGNER_PATH=$(find ${ANDROID_HOME}/build-tools/ -name apksigner 2>/dev/null | head -n 1) && \
    if [ -z "$APK_SIGNER_PATH" ]; then echo "Error: apksigner not found!" && exit 1; else echo "Found apksigner at: ${APK_SIGNER_PATH}" && ${APK_SIGNER_PATH} --version; fi

# نصب Python و وابستگی‌ها
RUN pip3 install --no-cache-dir flask requests gunicorn werkzeug

# تنظیم کارگاه
WORKDIR /app
COPY . .

ENV PORT=5000
ENV APK_SIGNER_PATH=${APK_SIGNER_PATH}
CMD ["sh", "-c", "echo 'Using APK_SIGNER_PATH at runtime: ${APK_SIGNER_PATH}' && gunicorn --bind 0.0.0.0:${PORT} app:app"]
