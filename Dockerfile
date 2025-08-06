FROM python:3.13-slim

# نصب پیش‌نیازها
RUN apt-get update && apt-get install -y openjdk-21-jdk wget unzip

# تنظیم محیط Android SDK
ENV ANDROID_SDK_ROOT=/opt/android-sdk
RUN mkdir -p ${ANDROID_SDK_ROOT}/cmdline-tools
RUN wget -q https://dl.google.com/android/repository/commandlinetools-linux-9477386_latest.zip -O /tmp/cmdline-tools.zip
RUN unzip -q /tmp/cmdline-tools.zip -d ${ANDROID_SDK_ROOT}/cmdline-tools
RUN mv ${ANDROID_SDK_ROOT}/cmdline-tools/cmdline-tools ${ANDROID_SDK_ROOT}/cmdline-tools/latest

# نصب build-tools و platform-tools با دیباگ
ENV PATH=${PATH}:${ANDROID_SDK_ROOT}/cmdline-tools/latest/bin:${ANDROID_SDK_ROOT}/build-tools/34.0.0:${ANDROID_SDK_ROOT}/platform-tools
RUN echo "Checking sdkmanager..." && \
    sdkmanager --sdk_root=${ANDROID_SDK_ROOT} "build-tools;34.0.0" "platform-tools" && \
    echo "Verifying tools..." && \
    ls ${ANDROID_SDK_ROOT}/build-tools/34.0.0/ && \
    ls ${ANDROID_SDK_ROOT}/platform-tools/ && \
    which zipalign && \
    zipalign --version

# تنظیم کارگاه
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=5000
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "app:app"]
