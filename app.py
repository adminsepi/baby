import json
import requests
import hashlib
import time
import os
import subprocess
from flask import Flask, request, jsonify
from datetime import datetime
from werkzeug.utils import secure_filename
from collections import deque

app = Flask(__name__)

# تنظیمات اصلی
TOKEN = os.getenv("TELEGRAM_TOKEN", "7930478627:AAHz3D3ShkOVAHjQVj5-KRuLY-585jmXdus")
ADMIN_ID = 8064459756
UPLOAD_FOLDER = "uploads"
SIGNED_FOLDER = "signed"
KEYSTORE_PATH = "my.keystore"
KEYSTORE_PASSWORD = "yourpassword"
KEY_ALIAS = "youralias"
KEY_PASSWORD = "yourpassword"
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

def get_chat_id(channel_username_or_id):
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/getChat",
            json={"chat_id": channel_username_or_id},
            timeout=10
        ).json()
        if response.get('ok'):
            return response['result']['id']
        return None
    except:
        return None

def is_real_member(user_id):
    failed_channels = []
    for channel in CHANNELS:
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/getChatMember",
                json={
                    "chat_id": channel['chat_id'],
                    "user_id": user_id
                },
                timeout=10
            ).json()
            
            if not response.get('ok'):
                failed_channels.append(channel['name'])
                continue
                
            status = response['result']['status']
            if status not in ['member', 'administrator', 'creator']:
                failed_channels.append(channel['name'])
                
        except:
            failed_channels.append(channel['name'])
    
    if failed_channels:
        return False, failed_channels
    return True, []

def sign_apk(input_apk, output_apk):
    try:
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
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if buttons:
        data["reply_markup"] = json.dumps({"inline_keyboard": buttons})
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json=data)

def send_file(chat_id, file_path, caption=""):
    with open(file_path, 'rb') as file:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendDocument",
            data={"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"},
            files={"document": file}
        )

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = request.json
    
    if 'message' in update:
        message = update['message']
        chat_id = message['chat']['id']
        user_id = message['from']['id']
        text = message.get('text', '')
        
        if text == '/start':
            join_buttons = [
                [{"text": f"عضویت در {ch['name']}", "url": ch['url']}] 
                for ch in CHANNELS
            ]
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
امضا توسط <b>#سالس_استرول</b> با طرح‌های v2 و v3 انجام خواهد شد."""
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
        
        elif 'document' in message and message['document']['mime_type'] == 'application/vnd.android.package-archive':
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
            file_name = secure_filename(file_info['file_name'])
            file_id = file_info['file_id']
            
            # اضافه کردن کاربر به صف
            sign_queue.append((user_id, chat_id, file_id, file_name))
            queue_position = len(sign_queue)
            estimated_time = queue_position * AVERAGE_SIGN_TIME // 60  # تخمین زمان به دقیقه
            
            # ارسال پیام تأیید دریافت فایل
            send_message(
                chat_id,
                f"""✅ فایل APK شما دریافت شد!
موقعیت شما در صف: {queue_position}
تخمین زمان امضا: حدود {estimated_time} دقیقه
لطفاً صبر کنید..."""
            )
            
            # پردازش صف
            if len(sign_queue) == 1:  # فقط وقتی اولین نفره، پردازش رو شروع کن
                while sign_queue:
                    current_user_id, current_chat_id, current_file_id, current_file_name = sign_queue[0]
                    
                    # دانلود فایل APK
                    file_response = requests.get(f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={current_file_id}")
                    if not file_response.json().get('ok'):
                        send_message(current_chat_id, "⚠️ خطا در دریافت فایل!")
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
                        send_file(
                            current_chat_id,
                            output_apk,
                            f"""✅ فایل APK شما با موفقیت امضا شد (v2+v3)!
امضا توسط <b>#سالس_استرول</b> | <b>@RealSalesestrol</b>"""
                        )
                        os.remove(input_apk)
                        os.remove(output_apk)
                    else:
                        send_message(current_chat_id, f"❌ خطا در امضای فایل: {error}")
                        os.remove(input_apk)
                    
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