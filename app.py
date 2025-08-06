import json
import requests
import os
import subprocess
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from collections import deque

app = Flask(__name__)

# تنظیمات اصلی
TOKEN = os.getenv("TELEGRAM_TOKEN", "7977369475:AAElCnt-uMl5XtrONdIVILTvRcyRQQqr2ik")
ADMIN_ID = 7934946400
UPLOAD_FOLDER = "uploads"
SIGNED_FOLDER = "signed"
KEYSTORE_PATH = "my.keystore"
KEYSTORE_PASSWORD = "123456"  # رمز keystore که ساختیم
KEY_ALIAS = "mykey"          # alias keystore که ساختیم
KEY_PASSWORD = "123456"      # رمز keystore که ساختیم
AVERAGE_SIGN_TIME = 30  # زمان متوسط امضا به ثانیه

# ایجاد پوشه‌ها
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SIGNED_FOLDER, exist_ok=True)

# سیستم صف
sign_queue = deque()

# تنظیمات کانال‌ها و گروه‌ها
CHANNELS = [
    {
        "name": "کانال پشتیبانی #سالس_استرول",
        "url": "https://t.me/salesestrol",
        "chat_id": -1002721560354
    },
    {
        "name": "کانال اختصاصی■VIP■",
        "url": "https://t.me/+XgPHewjiAdc1ZmI8",
        "chat_id": -1002337225404
    },
    {
        "name": "گروه چت و مشورت🔞",
        "url": "https://t.me/+EKFD_UpMaEpjODc0",
        "chat_id": -1002778968668
    }
]

def is_real_member(user_id):
    failed_channels = []
    for channel in CHANNELS:
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/getChatMember",
                json={"chat_id": channel['chat_id'], "user_id": user_id},
                timeout=10
            ).json()
            if not response.get('ok') or response['result']['status'] not in ['member', 'administrator', 'creator']:
                failed_channels.append(channel['name'])
        except Exception as e:
            failed_channels.append(channel['name'])
    return (False, failed_channels) if failed_channels else (True, [])

def sign_apk(input_apk, output_apk):
    try:
        if not os.path.exists(KEYSTORE_PATH):
            return False, f"خطا: فایل {KEYSTORE_PATH} پیدا نشد!"

        aligned_apk = os.path.join(SIGNED_FOLDER, "aligned_" + secure_filename(input_apk))
        subprocess.run(
            ["zipalign", "-f", "-v", "4", input_apk, aligned_apk],
            check=True,
            capture_output=True,
            text=True
        )

        subprocess.run(
            [
                "apksigner", "sign",
                "--ks", KEYSTORE_PATH,
                "--ks-key-alias", KEY_ALIAS,
                "--ks-pass", f"pass:{KEYSTORE_PASSWORD}",
                "--key-pass", f"pass:{KEY_PASSWORD}",
                "--v1-signing-enabled", "false",
                "--v2-signing-enabled", "true",
                "--v3-signing-enabled", "true",
                "--out", output_apk,
                aligned_apk
            ],
            check=True,
            capture_output=True,
            text=True
        )
        return True, None
    except subprocess.CalledProcessError as e:
        return False, f"خطا در امضا: {e.stderr}"
    except Exception as e:
        return False, f"خطای عمومی: {str(e)}"

def send_message(chat_id, text, buttons=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if buttons:
        data["reply_markup"] = json.dumps({"inline_keyboard": buttons})
    try:
        response = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json=data)
        return response.json().get('ok')
    except Exception as e:
        send_message(ADMIN_ID, f"خطا در ارسال پیام به {chat_id}: {str(e)}")
        return False

def send_file(chat_id, file_path, caption=""):
    try:
        with open(file_path, 'rb') as file:
            response = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendDocument",
                data={"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"},
                files={"document": file}
            )
        return response.json().get('ok')
    except Exception as e:
        send_message(ADMIN_ID, f"خطا در ارسال فایل به {chat_id}: {str(e)}")
        return False

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    try:
        update = request.json
    except Exception as e:
        send_message(ADMIN_ID, f"خطا در دریافت درخواست: {str(e)}")
        return jsonify({"status": "error"})

    if 'message' in update:
        message = update['message']
        chat_id = message['chat']['id']
        user_id = message['from']['id']
        text = message.get('text', '')

        if text == '/start':
            join_buttons = [[{"text": f"عضویت در {ch['name']}", "url": ch['url']}] for ch in CHANNELS]
            join_buttons.append([{"text": "تایید عضویت ✅", "callback_data": "verify_me"}])
            send_message(
                chat_id,
                """💥 پیام ادمین <b>#سالس_استرول</b>: 💥
🆔️ PV SUPPORTER: <b>@RealSalesestrol</b>
🔐 برای امضای فایل APK (v2+v3)، لطفاً در کانال‌ها و گروه زیر عضو شوید:""",
                join_buttons
            )

        elif text == '/sign':
            is_member, failed_channels = is_real_member(user_id)
            if is_member:
                send_message(
                    chat_id,
                    """🖋 لطفاً فایل APK خود را آپلود کنید.
امضا توسط <b>#سالس_استرول</b> با طرح‌های v2 و v3 (سازگار با اندروید 7.0+) انجام خواهد شد."""
                )
            else:
                failed_channel_names = ", ".join(failed_channels)
                send_message(
                    chat_id,
                    f"""⚠️ شما هنوز در موارد زیر عضو نشده‌اید:
{failed_channel_names}

لطفاً ابتدا در کانال‌ها و گروه <b>#سالس_استرول</b> عضو شوید و دوباره تلاش کنید.""",
                    [[{"text": "عضویت در کانال‌ها و گروه", "url": CHANNELS[0]['url']}], 
                     [{"text": "تلاش مجدد", "callback_data": "verify_me"}]]
                )

        elif 'document' in message and message['document'].get('mime_type') == 'application/vnd.android.package-archive':
            is_member, failed_channels = is_real_member(user_id)
            if not is_member:
                failed_channel_names = ", ".join(failed_channels)
                send_message(
                    chat_id,
                    f"""⚠️ شما هنوز در موارد زیر عضو نشده‌اید:
{failed_channel_names}

لطفاً ابتدا در کانال‌ها و گروه <b>#سالس_استرول</b> عضو شوید.""",
                    [[{"text": "عضویت در کانال‌ها و گروه", "url": CHANNELS[0]['url']}], 
                     [{"text": "تلاش مجدد", "callback_data": "verify_me"}]]
                )
                return jsonify({"status": "ok"})

            file_info = message['document']
            file_name = secure_filename(file_info.get('file_name', 'unknown.apk'))
            file_id = file_info['file_id']

            # چک کردن حجم فایل
            file_size = file_info.get('file_size', 0) / (1024 * 1024)  # تبدیل به مگابایت
            if file_size > 50:
                send_message(chat_id, "⚠️ فایل APK خیلی بزرگه! حداکثر حجم مجاز 50 مگابایته.")
                return jsonify({"status": "ok"})

            # اضافه کردن به صف
            sign_queue.append((user_id, chat_id, file_id, file_name))
            queue_position = len(sign_queue)
            estimated_time = queue_position * AVERAGE_SIGN_TIME // 60

            if not send_message(
                chat_id,
                f"""✅ فایل APK شما ({file_name}) دریافت شد!
موقعیت شما در صف: {queue_position}
تخمین زمان امضا: حدود {estimated_time} دقیقه
لطفاً صبر کنید..."""
            ):
                send_message(ADMIN_ID, f"خطا در ارسال پیام تأیید به {chat_id} برای فایل {file_name}")

            if len(sign_queue) == 1:
                while sign_queue:
                    current_user_id, current_chat_id, current_file_id, current_file_name = sign_queue[0]
                    try:
                        file_response = requests.get(f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={current_file_id}")
                        if not file_response.json().get('ok'):
                            send_message(current_chat_id, "⚠️ خطا در دریافت فایل از تلگرام!")
                            send_message(ADMIN_ID, f"خطا در دریافت فایل {current_file_name} برای کاربر {current_user_id}")
                            sign_queue.popleft()
                            continue

                        file_path = file_response.json()['result']['file_path']
                        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
                        input_apk = os.path.join(UPLOAD_FOLDER, current_file_name)

                        with open(input_apk, 'wb') as f:
                            f.write(requests.get(file_url).content)

                        output_apk = os.path.join(SIGNED_FOLDER, "signed_" + current_file_name)
                        success, error = sign_apk(input_apk, output_apk)

                        if success:
                            if send_file(
                                current_chat_id,
                                output_apk,
                                f"""✅ فایل APK شما با موفقیت امضا شد (v2+v3، سازگار با اندروید 7.0+)!
امضا توسط <b>ربات پیشرفته #عمو_سالس</b> | <b>@RealSalesestrol</b>"""
                            ):
                                os.remove(input_apk)
                                os.remove(output_apk)
                            else:
                                send_message(current_chat_id, "❌ خطا در ارسال فایل امضاشده!")
                                send_message(ADMIN_ID, f"خطا در ارسال فایل امضاشده {current_file_name} به کاربر {current_user_id}")
                        else:
                            send_message(current_chat_id, f"❌ خطا در امضای فایل: {error}")
                            send_message(ADMIN_ID, f"خطا در امضای فایل {current_file_name} برای کاربر {current_user_id}: {error}")
                            os.remove(input_apk)
                    except Exception as e:
                        send_message(current_chat_id, f"❌ خطا در پردازش فایل: {str(e)}")
                        send_message(ADMIN_ID, f"خطا در پردازش فایل {current_file_name} برای کاربر {current_user_id}: {str(e)}")
                    sign_queue.popleft()

    elif 'callback_query' in update:
        callback = update['callback_query']
        chat_id = callback['message']['chat']['id']
        user_id = callback['from']['id']
        data = callback['data']

        if data == 'verify_me':
            is_member, failed_channels = is_real_member(user_id)
            if is_member:
                send_message(
                    chat_id,
                    """🎉 عضویت شما تأیید شد!
برای امضای فایل APK، از دستور /sign استفاده کنید و سپس فایل APK خود را آپلود کنید.
مدیریت: <b>#سالس_استرول</b> | <b>@RealSalesestrol</b>"""
                )
            else:
                failed_channel_names = ", ".join(failed_channels)
                send_message(
                    chat_id,
                    f"""⚠️ شما هنوز در موارد زیر عضو نشده‌اید:
{failed_channel_names}

لطفاً ابتدا در کانال‌ها و گروه <b>#سالس_استرول</b> عضو شوید و دوباره تلاش کنید.""",
                    [[{"text": "عضویت در کانال‌ها و گروه", "url": CHANNELS[0]['url']}], 
                     [{"text": "تلاش مجدد", "callback_data": "verify_me"}]]
                )

    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))
