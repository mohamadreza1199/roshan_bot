import asyncio
import logging
from aiogram import Router
router = Router()
from datetime import datetime
import jdatetime
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
# تعریف دکمه‌های مختلف
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="شروع مجدد 🔄")]
        ],
        resize_keyboard=True
    )
    return keyboard
from aiogram.dispatcher.middlewares.base import BaseMiddleware
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable

class AlwaysShowMainMenuMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, Message):
            data["reply_markup"] = get_main_menu()
        return await handler(event, data)

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
def get_number_keyboard(min_num, max_num):
    buttons = [
        [InlineKeyboardButton(text=str(i), callback_data=f"number_{i}")]
        for i in range(min_num, max_num + 1)
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import pyodbc
import asyncio

# کش کالاها
all_products = []

# دریافت لیست کالاها از دیتابیس و ذخیره در کش
def refresh_products():
    global all_products
    try:
        conn = pyodbc.connect(
            "DRIVER={SQL Server};"
            "SERVER=94.183.153.185,1433;"
            "DATABASE=Total;"
            "UID=robot_user;"
            "PWD=123456;"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM tGood")
        all_products = [row[0] for row in cursor.fetchall()]

        print(f"✅ لیست کالاها به‌روز شد: {len(all_products)} کالا")

        # ذخیره توی فایل متنی برای بررسی
        with open("list_of_goods.txt", "w", encoding="utf-8") as f:
            for item in all_products:
                f.write(item + "\n")

    except Exception as e:
        print(f"❌ خطا در دریافت کالاها: {e}")
# جستجو در کش
def search_from_cache(search_text):
    search_text = search_text.strip().replace("‌", " ")  # حذف نیم‌فاصله‌های احتمالی
    if not search_text:
        return []

    search_text = search_text.lower()  # تطبیق بدون حساسیت به حروف بزرگ/کوچک
    results = []

    for name in all_products:
        name_lower = name.lower()
        if search_text in name_lower:
            score = name_lower.count(search_text)
            results.append((score, name))

    results.sort(reverse=True)
    return [name for _, name in results][:20]
# اجرای هر ۵ دقیقه برای آپدیت کش
async def auto_refresh_products():
    while True:
        refresh_products()
        await asyncio.sleep(300)  # هر ۵ دقیقه

# تابع برای بارگذاری نام کالاها از فایل JSON
def load_item_names():
    try:
        with open("items.json", "r", encoding="utf-8") as file:
            return json.load(file)  # تبدیل محتویات فایل JSON به دیکشنری
    except Exception as e:
        print(f"⚠️ خطا در بارگذاری لیست کالاها: {e}")
        return {}  # در صورت خطا، یک دیکشنری خالی برمی‌گرداند

# لود کردن لیست کالاها
ITEM_NAMES = load_item_names()

# تعداد ستون‌ها در هر ردیف
COLUMNS = 2  # این مقدار را تغییر بده تا دکمه‌ها در ردیف‌های ۲ یا ۴ تایی باشند

# ایجاد کیبورد دینامیک با چینش چند ستونه
def generate_item_keyboard():
    keyboard = []
    row = []

    for key, name in ITEM_NAMES.items():
        row.append(InlineKeyboardButton(text=name, callback_data=key))

        # اگر تعداد دکمه‌های ردیف به مقدار ستون‌ها رسید، به کیبورد اضافه شود
        if len(row) == COLUMNS:
            keyboard.append(row)
            row = []

    # اگر دکمه‌های باقی‌مانده در ردیف ناقص بود، اضافه شود
    if row:
        keyboard.append(row)

    # افزودن دکمه پایان به‌صورت جداگانه
    keyboard.append([InlineKeyboardButton(text="✅ پــایـــان", callback_data="end_selection")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# لود کردن لیست کالاها در هنگام شروع برنامه
ITEM_NAMES = load_item_names()

# توکن ربات
API_TOKEN = "7744253886:AAH14uw33bXzQFnMUL6eJUraDNtjRaWvcOI"
GROUP_ID = "-1002287304966"  # 🔹 آیدی کانال خود را اینجا بگذارید

# تنظیمات لاگ
logging.basicConfig(level=logging.INFO)

# ایجاد شیء ربات و Dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
dp.message.middleware(AlwaysShowMainMenuMiddleware())

class Form(StatesGroup):
    waiting_for_product_name = State()
    waiting_for_net_weight = State()
    waiting_for_package_weight = State()
    waiting_for_package_count = State()
    waiting_for_remaining_quantity = State()
    waiting_for_item_count = State()  # این را اضافه کن
    waiting_for_bulk_product_name = State()  # برای نام کالای فله
    waiting_for_bulk_product_weight = State()  # برای وزن خالص کالای فله
    waiting_for_item = State()
    waiting_for_quantity = State()
    waiting_for_total_packs = State()
    waiting_for_total_package_weight = State()
    waiting_for_package_count_final = State()
    waiting_for_product_selection = State()
    waiting_for_bulk_product_selection = State()
    waiting_for_weight = State()

# هندلر دکمه "شروع مجدد"
@dp.message(F.text == "شروع مجدد 🔄")
async def restart_process(message: types.Message, state: FSMContext):
    await state.clear()  # پاک کردن تمام state ها
    await send_welcome(message, state)  # اجرای همان دستور /start

@dp.message(Command("start"))
async def send_welcome(message: types.Message, state: FSMContext):
    await message.answer("سلام! به ربات فروشگاه روشن خوش آمدید:", reply_markup=get_main_menu())
    await state.set_state(Form.waiting_for_product_name)  # وضعیت دریافت نام کاربر

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="انتخاب نام کاربر", callback_data="select_user")]
        ]
    )
    await message.answer("برای انتخاب نام خود روی دکمه زیر کلیک کنید:", reply_markup=keyboard)

# پردازش انتخاب نام کاربر
@dp.callback_query(F.data == "select_user")
async def select_user(callback: types.CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="محمدرضا سقا", callback_data="mohammadreza")],
            [InlineKeyboardButton(text="علی سقا", callback_data="ali")],
            [InlineKeyboardButton(text="اکرم خلیلی", callback_data="akram")],
            [InlineKeyboardButton(text="محبوب حیدری", callback_data="mahdavi")],
            [InlineKeyboardButton(text="اتوحساب", callback_data="amir")]
        ]
    )
    await callback.message.edit_text("لطفاً نام کاربر را انتخاب کنید:", reply_markup=keyboard)


# پردازش انتخاب نام
@dp.callback_query(F.data.in_(["mohammadreza", "ali", "akram", "mahdavi", "amir"]))
async def process_name(callback_query: types.CallbackQuery, state: FSMContext):
    user_name_map = {
        "mohammadreza": "محمدرضا سقا",
        "ali": "علی سقا",
        "akram": "اکرم خلیلی",
        "mahdavi": "محبوب حیدری",
        "amir": "اتو حساب"
    }

    user_name = user_name_map.get(callback_query.data)  # دریافت نام فارسی از نقشه
    if user_name:
        await state.update_data(user_name=user_name)  # ذخیره نام فارسی در state
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="گزارش صندوق", callback_data="box_report")],
                [InlineKeyboardButton(text="گزارش بسته بندی", callback_data="production_report")],
                [InlineKeyboardButton(text="گزارش تولید کالا", callback_data="product_report")]  # اینجا کاما اضافه شد
    ]
)     
        await callback_query.message.edit_text(f"نام شما ذخیره شد: {user_name}\nحالا می‌توانید گزارش ثبت کنید.", reply_markup=keyboard)
    else:
        await callback_query.message.edit_text("خطا: نام انتخاب شده صحیح نیست.")
# پردازش انتخاب گزارش بسته بندی
@dp.callback_query(F.data == "production_report") 
async def production_report(callback: types.CallbackQuery, state: FSMContext):
    now = jdatetime.datetime.now().strftime("%Y/%m/%d %H:%M")
    user_data = await state.get_data()
    
    user_name = user_data.get("user_name", "نامشخص")
    
    await state.update_data(date_time=now, user_name=user_name)

    await callback.message.edit_reply_markup(reply_markup=None)

    await callback.message.answer(
        f"\U0001F4CB گزارش بسته بندی\n"
        f"\U0001F4C5 تاریخ و ساعت: {now}\n"
        f"\U0001F464 نام کاربر: {user_name}"
    )
    await callback.message.answer("نام کالایی که میخواهید بسته بندی کنید چیست؟ (روشن)")

    await state.set_state(Form.waiting_for_product_name)

@dp.message(Form.waiting_for_product_name)
async def process_product_name(message: types.Message, state: FSMContext):
    search_term = message.text

    product_names = search_from_cache(search_term)

    if not product_names:
        await message.answer("کالایی با این نام پیدا نشد. لطفاً مجدداً وارد کنید.")
        return

    # ذخیره لیست کالاها برای استفاده بعدی در انتخاب
    await state.update_data(product_list=product_names)

    # ساخت دکمه‌ها با index
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"select_product_{i}")]
        for i, name in enumerate(product_names)
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer("لطفاً کالای موردنظر را از لیست زیر انتخاب کنید:", reply_markup=markup)

# دریافت نام کالا
@dp.callback_query(F.data.startswith("select_product_"))
async def select_product_callback(callback: types.CallbackQuery, state: FSMContext):
    index = int(callback.data.split("_")[-1])
    data = await state.get_data()
    product_list = data.get("product_list", [])

    if index >= len(product_list):
        await callback.message.answer("❌ انتخاب نامعتبر. لطفاً دوباره تلاش کنید.")
        return

    product_name = product_list[index]
    await state.update_data(product_name=product_name)

    await callback.message.edit_text(f"✅ کالای انتخاب‌شده: {product_name}")
    await callback.message.answer("چند قلم کالا بسته‌بندی شده است؟ لطفاً یک عدد وارد کنید.")
    await state.set_state(Form.waiting_for_item_count)
    
@router.message(Form.waiting_for_item_count)
async def process_product_count(message: types.Message, state: FSMContext):
    if message.text.isdigit():  # بررسی اینکه مقدار واردشده عدد است
        number = int(message.text)
        if 1 <= number <= 15:  # بررسی محدوده عدد
            await state.update_data(item_count=number)
            await message.answer(f"تعداد {number} ثبت شد. مرحله بعدی چیست؟")  
            # 🔹 اینجا می‌توانی مرحله بعدی را مشخص کنی
            
            await state.clear()  # پاک کردن وضعیت
        else:
            await message.answer("لطفاً عددی بین 1 تا 15 وارد کنید.")
    else:
        await message.answer("لطفاً یک عدد معتبر وارد کنید.")
# دریافت تعداد اقلام بسته بندی شده
@dp.message(Form.waiting_for_item_count)
async def process_item_count(message: types.Message, state: FSMContext):
    count = int(message.text)
    await state.update_data(item_count=count, current_step=1, bulk_items=[])
    await message.answer("نام کالای فله را وارد کنید:")
    await state.set_state(Form.waiting_for_bulk_product_name)  # اینجا اصلاح شد

@dp.message(Form.waiting_for_bulk_product_name)
async def process_bulk_product_name(message: types.Message, state: FSMContext):
    search_term = message.text.strip()
    product_names = search_from_cache(search_term)  # ← کشِ محصولات

    if not product_names:
        await message.answer("❌ کالای فله‌ای با این نام پیدا نشد. لطفاً دوباره تلاش کنید.")
        return

    # ذخیره در استیت برای استفاده در callback
    await state.update_data(bulk_product_list=product_names)

    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"select_bulk_product_{i}")]
        for i, name in enumerate(product_names)
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer("کالای فله موردنظر را از لیست زیر انتخاب کنید:", reply_markup=markup)

@dp.callback_query(F.data.startswith("select_bulk_product_"))
async def select_bulk_product_callback(callback: types.CallbackQuery, state: FSMContext):
    index = int(callback.data.split("_")[-1])
    data = await state.get_data()
    bulk_list = data.get("bulk_product_list", [])
    bulk_items = data.get("bulk_items", [])

    if index >= len(bulk_list):
        await callback.message.answer("❌ انتخاب نامعتبر. لطفاً دوباره تلاش کنید.")
        return

    bulk_product_name = bulk_list[index]
    bulk_items.append({"name": bulk_product_name, "weight": None, "remaining": None})
    await state.update_data(bulk_items=bulk_items)

    await callback.message.edit_text(f"✅ کالای فله انتخاب‌شده: {bulk_product_name}")
    await callback.message.answer(f"📦 وزن کالای '{bulk_product_name}' داخل بسته چقدر است؟")
    await state.set_state(Form.waiting_for_package_weight)

@dp.message(Form.waiting_for_net_weight)
async def process_net_weight(message: types.Message, state: FSMContext):
    data = await state.get_data()
    bulk_items = data.get("bulk_items", [])

    try:
        weight = float(message.text)
    except ValueError:
        await message.answer("❌ لطفاً مقدار عددی صحیحی برای وزن خالص وارد کنید.")
        return

    # ذخیره وزن خالص
    bulk_items[-1]["weight"] = weight  
    await state.update_data(bulk_items=bulk_items)

    # حالا بعد از اینکه وزن خالص وارد شد، سوال بعدی رو بپرس:
    await message.answer(f"🔢 باقی‌مانده کالای '{bulk_items[-1]['name']}' چقدر است؟")
    await state.set_state(Form.waiting_for_remaining_quantity)

@dp.message(Form.waiting_for_package_weight)
async def process_package_weight(message: types.Message, state: FSMContext):
    try:
        package_weight = float(message.text.strip())
    except ValueError:
        await message.answer("❌ لطفاً یک مقدار عددی معتبر برای وزن هر بسته وارد کنید.")
        return

    # به‌روزرسانی وزن بسته در آخرین کالای اضافه شده
    data = await state.get_data()
    bulk_items = data.get("bulk_items", [])
    if not bulk_items:  # اگر لیست خالی بود، یک مقدار اولیه اضافه کن
        bulk_items.append({"package_weight": 0})
    bulk_items[-1]["package_weight"] = package_weight  # حالا مقدار را تنظیم کن
    await state.update_data(bulk_items=bulk_items)

    # درخواست وزن خالص کالای تحویل گرفته شده
    item_name = bulk_items[-1].get('name', "کالای نامشخص")
    await message.answer(f"⚖️ وزن خالص کالای '{item_name}' تحویل گرفته شده چقدر است؟")
    await state.set_state(Form.waiting_for_net_weight)

@dp.message(Form.waiting_for_remaining_quantity)
async def process_remaining_quantity(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_step = data.get("current_step", 1)
    item_count = data.get("item_count", 1)
    bulk_items = data.get("bulk_items", [])

    try:
        remaining = float(message.text)  # تبدیل ورودی به عدد اعشاری
    except ValueError:
        await message.answer("❌ لطفاً مقدار عددی صحیحی برای باقی‌مانده وارد کنید.")
        return

    # ذخیره مقدار باقی‌مانده در لیست
    bulk_items[-1]["remaining"] = remaining  
    await state.update_data(bulk_items=bulk_items)

    # بررسی ادامه روند دریافت اطلاعات کالاها
    if current_step < item_count:
        current_step += 1
        await state.update_data(current_step=current_step)
        await message.answer(f"📝 نام کالای فله {current_step} را وارد کنید:")
        await state.set_state(Form.waiting_for_bulk_product_name)
    else:
        # نمایش خلاصه اطلاعات
        summary = "\n".join([
            f"{i+1}. {item['name']} - وزن داخل هر بسته: {item.get('package_weight', 'نامشخص')} کیلوگرم - وزن خالص تحویلی: {item['weight']} کیلوگرم - باقی‌مانده: {item['remaining']} کیلوگرم"
            for i, item in enumerate(bulk_items)
        ])
        await message.answer(f"✅ ثبت اطلاعات به پایان رسید:\n{summary}", reply_markup=get_main_menu())

        await message.answer("📦 تعداد کل بسته‌هایی که بسته‌بندی شده است را وارد کنید:")
        await state.set_state(Form.waiting_for_package_count_final)

@dp.message(Form.waiting_for_package_count_final)
async def process_package_count_final(message: types.Message, state: FSMContext):
    try:
        package_count = int(message.text.strip())
        await state.update_data(final_package_count=package_count)

        # دریافت اطلاعات قبلی از state
        data = await state.get_data()
        bulk_items = data.get("bulk_items", [])
        last_item = bulk_items[-1] if bulk_items else {}

        # استخراج مقادیر لازم از آخرین کالای ثبت‌شده
        bulk_weight = last_item.get("weight", "نامشخص")
        package_weight = last_item.get("package_weight", "نامشخص")
        remaining_weight = last_item.get("remaining", "نامشخص")

        # محاسبه وزن نهایی از تعداد و وزن هر بسته
        try:
            total_pack_weight = float(package_weight) * package_count
        except:
            total_pack_weight = "نامشخص"

        # ذخیره‌سازی در state برای استفاده در گزارش نهایی
        await state.update_data(
            bulk_weight=bulk_weight,
            package_weight=package_weight,
            remaining_weight=remaining_weight,
            total_pack_weight=total_pack_weight
        )

        # ادامه مراحل (مثلاً انتخاب کالای مصرفی بعدی یا رفتن به منو)
        await message.answer("📦 کالای مصرفی بسته‌بندی‌شده را انتخاب کنید:", reply_markup=generate_item_keyboard())

    except ValueError:
        await message.answer("❌ لطفاً یک عدد صحیح برای تعداد بسته‌ها وارد کنید.")

@dp.message(Form.waiting_for_total_package_weight)
async def process_total_package_weight(message: types.Message, state: FSMContext):
    try:
        total_weight = float(message.text)
        await state.update_data(total_pack_weight=total_weight)


    except ValueError:
        await message.answer("❌ لطفاً عدد صحیحی برای وزن کل وارد کنید.")

    # حالا سوال بعدی
    await message.answer("📦 تعداد کل بسته‌هایی که بسته‌بندی شده است را وارد کنید:")
    await state.set_state(Form.waiting_for_package_count_final)

@dp.message(Form.waiting_for_package_count_final)
async def process_package_count_final(message: types.Message, state: FSMContext):
    try:
        package_count = int(message.text.strip())
    except ValueError:
        await message.answer("❌ لطفاً یک عدد صحیح برای تعداد بسته‌ها وارد کنید.")
        return

    await state.update_data(final_package_count=package_count)

    # مقداردهی اولیه لیست انتخاب‌شده‌ها
    await state.update_data(selected_items=[])

    await message.answer(
        "📦 کالای مصرفی بسته‌بندی‌شده را انتخاب کنید:",
        reply_markup=generate_item_keyboard()
    )

@dp.callback_query(lambda c: c.data.startswith("item_"))
async def process_selected_item(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_items = data.get("selected_items", [])

    item_code = callback_query.data  # مثلا item_1 یا item_5

    if item_code not in selected_items:
        selected_items.append(item_code)
        await callback_query.answer(f"✅ {ITEM_NAMES.get(item_code, item_code)} اضافه شد")
    else:
        selected_items.remove(item_code)
        await callback_query.answer(f"❌ {ITEM_NAMES.get(item_code, item_code)} حذف شد")

    await state.update_data(selected_items=selected_items)

# تعریف تابع ارسال گزارش به کانال
THREAD_ID = 1868  # عدد آیدی تاپیک دلخواه
GROUP_ID = -1002287304966  # آیدی گروه/کانال شما

async def send_report_to_channel(report_message):
    try:
        await bot.send_message(
            chat_id=GROUP_ID,
            text=report_message,
            message_thread_id=THREAD_ID  # اضافه شده
        )
        print("✅ گزارش با موفقیت در تاپیک ارسال شد.")
    except Exception as e:
        print(f"❌ خطا در ارسال گزارش به تاپیک: {e}")
@dp.callback_query(F.data.startswith("select_product_name_"))
async def handle_selected_product_name(callback: CallbackQuery, state: FSMContext):
    try:
        index = int(callback.data.split("_")[-1])
        data = await state.get_data()
        suggestions = data.get("suggestions_list", [])

        if index < len(suggestions):
            selected_name = suggestions[index]
            await state.update_data(product_name=selected_name)
            await callback.message.edit_text(
                f"✅ نام کالا ثبت شد: {selected_name}\n🔢 چند قلم کالا داخل این کالا وجود دارد؟"
            )
            await state.set_state(ProductReportForm.waiting_for_item_count)
            await callback.answer()
        else:
            await callback.answer("❌ گزینه نامعتبر است.", show_alert=True)

    except Exception as e:
        print("خطا در انتخاب کالا:", e)
        await callback.answer("❌ خطا در انتخاب کالا.", show_alert=True)
    
@dp.callback_query(lambda c: c.data == "end_selection")
async def process_end_selection(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    selected_items = data.get("selected_items", [])
    selected_items_text = "\n".join([f"✅ {ITEM_NAMES.get(item, item)}" for item in selected_items])

    # اطلاعات عمومی
    date_time = data.get("date_time", "نامشخص")
    user_name = data.get("user_name", "نامشخص")
    product_name = data.get("product_name", "نامشخص")
    item_count = data.get("item_count", "نامشخص")
    final_package_count = data.get("final_package_count", "نامشخص")

    # کالاهای فله‌ای
    bulk_items = data.get("bulk_items", [])
    bulk_summary = ""
    for i, item in enumerate(bulk_items):
        bulk_summary += (
            f"\n— {i+1}. {item.get('name', 'کالا')}:\n"
            f"   📦 وزن داخل بسته: {item.get('package_weight', 'نامشخص')} کیلوگرم\n"
            f"   ⚖️ وزن خالص تحویل‌شده: {item.get('weight', 'نامشخص')} کیلوگرم\n"
            f"   🔢 باقی‌مانده: {item.get('remaining', 'نامشخص')} کیلوگرم\n"
        )

    # محاسبه وزن نهایی بسته‌بندی‌شده فقط از مجموع وزن‌های داخل بسته
    total_pack_weight = round(sum(float(item.get("package_weight", 0) or 0) for item in bulk_items), 2)

    # ساخت گزارش نهایی
    report_message = (
        f"📦 گزارش نهایی بسته‌بندی 📦\n"
        f"-----------------------------\n"
        f"📅 تاریخ و ساعت: {date_time}\n"
        f"👤 نام کاربر: {user_name}\n"
        f"🛍 نام کالای نهایی: {product_name}\n"
        f"📦 تعداد اقلام فله: {item_count} عدد\n"
        f"{bulk_summary}\n"
        f"📦 تعداد کل بسته‌ها: {final_package_count} عدد\n"
        f"⚖️ وزن نهایی بسته‌بندی‌شده: {total_pack_weight} کیلوگرم\n"
        f"✅ **کالاهای مصرفی بسته‌بندی‌شده:**\n{selected_items_text}"
    )

    await callback_query.message.answer(report_message, reply_markup=get_main_menu())
    await send_report_to_channel(report_message)
    await state.clear()
    await callback_query.answer("✅ گزارش نهایی ثبت شد.")

@dp.callback_query(F.data == "box_report")
async def box_report(callback: types.CallbackQuery, state: FSMContext):
    # حذف دکمه‌های قبلی
    await callback.message.edit_reply_markup(reply_markup=None)

    # دریافت تاریخ و ساعت شمسی
    now = jdatetime.datetime.now().strftime("%Y/%m/%d %H:%M")

    # دریافت نام کاربر از state
    user_data = await state.get_data()
    user_name = user_data.get("user_name", "نامشخص")

    # ذخیره تاریخ و ساعت در state
    await state.update_data(date_time=now)

    # دکمه‌های انتخاب شیفت
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="شیفت صبح", callback_data="shift_morning")],
            [InlineKeyboardButton(text="شیفت عصر", callback_data="shift_evening")]
        ]
    )

    # ارسال پیام‌ها
    await callback.message.answer(f"📋 گزارش صندوق\n📅 تاریخ و ساعت: {now}\n👤 نام کاربر: {user_name}")
    await callback.message.answer("لطفاً شیفت را انتخاب کنید:", reply_markup=keyboard)

    await state.set_state(CashReportForm.waiting_for_shift)

@dp.callback_query(F.data.startswith("shift_"))
async def process_shift(callback: types.CallbackQuery, state: FSMContext):
    shift = "صبح" if callback.data == "shift_morning" else "عصر"
    await state.update_data(shift=shift)

    # فقط ارسال پیام جدید بدون حذف پیام قبلی
    await callback.message.answer("💰 مبلغ شارژ صندوق را وارد کنید:")

    await state.set_state(CashReportForm.waiting_for_cash_amount)
    await callback.answer()

from aiogram.fsm.state import State, StatesGroup

class CashReportForm(StatesGroup):
    waiting_for_cash_amount = State()
    waiting_for_total_cash = State()
    waiting_for_card_total = State()
    waiting_for_registered_amount = State()

@dp.message(CashReportForm.waiting_for_cash_amount)
async def process_cash_amount(message: types.Message, state: FSMContext):
    await state.update_data(cash_amount=message.text)
    await message.answer("💵 جمع کل وجه نقد را وارد کنید:")
    await state.set_state(CashReportForm.waiting_for_total_cash)

@dp.message(CashReportForm.waiting_for_total_cash)
async def process_total_cash(message: types.Message, state: FSMContext):
    await state.update_data(total_cash=message.text)
    await message.answer("🏦 جمع موجودی کارتخوان‌ها را وارد کنید:")
    await state.set_state(CashReportForm.waiting_for_card_total)

@dp.message(CashReportForm.waiting_for_card_total)
async def process_card_total(message: types.Message, state: FSMContext):
    await state.update_data(card_total=message.text)
    await message.answer("📊 مبلغ کارت به کارت را وارد کنید؟:")
    await state.set_state(CashReportForm.waiting_for_registered_amount)

@dp.message(CashReportForm.waiting_for_registered_amount)
async def process_registered_amount(message: types.Message, state: FSMContext):
    await state.update_data(registered_amount=message.text)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="بدون مغایرت", callback_data="no_discrepancy")],
            [InlineKeyboardButton(text="دارای مغایرت", callback_data="has_discrepancy")]
        ]
    )
    await message.answer("📌 وضعیت صندوق را مشخص کنید:", reply_markup=keyboard)

from aiogram.fsm.state import State, StatesGroup

class CashReportForm(StatesGroup):
    waiting_for_cash_amount = State()
    waiting_for_total_cash = State()
    waiting_for_card_total = State()
    waiting_for_registered_amount = State()
    waiting_for_notes = State()  # مرحله جدید برای دریافت توضیحات

from aiogram.fsm.state import State, StatesGroup

class CashReportForm(StatesGroup):
    waiting_for_cash_amount = State()
    waiting_for_total_cash = State()
    waiting_for_card_total = State()
    waiting_for_registered_amount = State()
    waiting_for_cash_description = State()  # 👈 اضافه کردن وضعیت جدید
    waiting_for_shift = State()

@dp.callback_query(F.data.in_(["no_discrepancy", "has_discrepancy"]))
async def process_discrepancy(callback: types.CallbackQuery, state: FSMContext):
    status = "بدون مغایرت" if callback.data == "no_discrepancy" else "دارای مغایرت"
    await state.update_data(status=status)
    
    await callback.message.edit_text("📝 لطفاً توضیحات صندوق را وارد کنید:")
    await state.set_state(CashReportForm.waiting_for_cash_description)  # 👈 تغییر وضعیت

async def send_cash_report_to_group(report_message):
    GROUP_ID = "-1002287304966"  # آیدی گروه
    THREAD_ID = 1962  # آیدی تاپیک مخصوص گزارش صندوق، عددی که خودت از قبل پیدا کردی

    try:
        await bot.send_message(
            chat_id=GROUP_ID,
            message_thread_id=THREAD_ID,
            text=report_message
        )
        print("✅ گزارش صندوق با موفقیت ارسال شد.")
    except Exception as e:
        print(f"❌ خطا در ارسال گزارش صندوق: {e}")

@dp.message(CashReportForm.waiting_for_cash_description)
async def process_cash_description(message: types.Message, state: FSMContext):
    await state.update_data(cash_description=message.text)
    
    data = await state.get_data()
    summary = (
        f"📋 گزارش صندوق:\n"
        f"📅 تاریخ و ساعت: {data['date_time']}\n"
        f"👤 نام کاربر: {data['user_name']}\n"
        f"🕒 شیفت: {data['shift']}\n"
        f"💰 مبلغ شارژ صندوق: {data['cash_amount']} تومان\n"
        f"💵 وجه نقد: {data['total_cash']} تومان\n"
        f"🏦 کارتخوان‌ها: {data['card_total']} تومان\n"
        f"📊 کارت به کارت: {data['registered_amount']} تومان\n"
        f"✅ وضعیت: {data['status']}\n"
        f"📝 توضیحات: {data['cash_description']}"  # 👈 اضافه کردن توضیحات
    )
    
    await message.answer(summary)
    await send_cash_report_to_group(summary)  # ارسال گزارش به گروه
    await state.clear()

# تعریف State جدید برای گزارش تولید کالا
class ProductReportForm(StatesGroup):
    waiting_for_product_name = State()          # مرحله دریافت نام کالای تولید شده
    waiting_for_item_count = State()            # مرحله دریافت تعداد اقلام داخل کالا
    waiting_for_each_item_name = State()        # مرحله دریافت نام هر قلم
    waiting_for_each_item_weight = State()      # مرحله دریافت وزن هر قلم
    confirming_report = State()                 # مرحله تأیید و ارسال گزارش نهایی

# شروع فرآیند تولید کالا
@dp.callback_query(F.data == "product_report")
async def start_product_report(callback: CallbackQuery, state: FSMContext):
    now = jdatetime.datetime.now().strftime("%Y/%m/%d %H:%M")
    user_data = await state.get_data()
    user_name = user_data.get("user_name", "نامشخص")

    await state.update_data(date_time=now, user_name=user_name)

    # حذف دکمه‌ها با ویرایش پیام
    await callback.message.edit_text(
        f"📋 گزارش تولید کالا\n"
        f"📅 تاریخ و ساعت: {now}\n"
        f"👤 نام کاربر: {user_name}"
    )

    # ارسال پیام جدید برای دریافت نام کالا
    await callback.message.answer("📦 نام کالای تولیدشده را وارد کنید:")
    await state.set_state(ProductReportForm.waiting_for_product_name)

@dp.message(ProductReportForm.waiting_for_product_name)
async def process_product_name_autocomplete(message: types.Message, state: FSMContext):
    search_text = message.text.strip()
    suggestions = search_from_cache(search_text)

    if not suggestions:
        await state.update_data(product_name=search_text)
        await message.answer(
            f"❌ هیچ کالایی با این نام پیدا نشد.\n✅ نام کالا ثبت شد: {search_text}\n🔢 چند قلم کالا داخل این کالا وجود دارد؟"
        )
        await state.set_state(ProductReportForm.waiting_for_item_count)
        return

    # ذخیره لیست پیشنهادات در state
    await state.update_data(suggestions_list=suggestions)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=item, callback_data=f"production_product_name_{i}")]
            for i, item in enumerate(suggestions)
        ]
    )

    await message.answer("❓ لطفاً یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("production_product_name_"))
async def handle_selected_product_name(callback: CallbackQuery, state: FSMContext):
    try:
        index = int(callback.data.split("_")[-1])
    except ValueError:
        await callback.answer("❌ انتخاب نامعتبر.")
        return

    data = await state.get_data()
    suggestions = data.get("suggestions_list", [])

    if not suggestions or index >= len(suggestions):
        await callback.answer("❌ لیست پیشنهادات نامعتبر یا خالی است.")
        return

    selected_name = suggestions[index]
    await state.update_data(product_name=selected_name)

    await callback.message.answer(
        f"✅ نام کالا ثبت شد: {selected_name}\n🔢 چند قلم کالا داخل این کالا وجود دارد؟"
    )
    await state.set_state(ProductReportForm.waiting_for_item_count)
    await callback.answer()
    
# هندلر دریافت تعداد اقلام
@dp.message(ProductReportForm.waiting_for_item_count)
async def process_item_count(message: types.Message, state: FSMContext):
    try:
        count = int(message.text.strip())
        await state.update_data(item_count=count, current_index=0, items=[])
        await message.answer("📝 نام قلم اول را وارد کنید:")
        await state.set_state(ProductReportForm.waiting_for_each_item_name)
    except:
        await message.answer("❌ لطفاً یک عدد معتبر وارد کنید.")

# اتو کمپلیت برای نام اقلام (autocomplete)
@dp.message(ProductReportForm.waiting_for_each_item_name)
async def process_each_item_name_autocomplete(message: Message, state: FSMContext):
    search_text = message.text.strip()
    suggestions = search_from_cache(search_text)

    if not suggestions:
        await update_item_and_ask_for_weight(state, search_text, message)
        return

    await state.update_data(last_suggestions=suggestions)

    keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=item, callback_data=f"select_each_item_name_{i}")]
        for i, item in enumerate(suggestions)
        ]
    )

    await message.answer("❓ لطفاً یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=keyboard)

# دکمه انتخاب قلم از لیست autocomplete
@dp.callback_query(F.data.startswith("select_each_item_name_"))
async def handle_selected_each_item_name(callback: CallbackQuery, state: FSMContext):
    try:
        index_str = callback.data.split("_")[-1]
        index = int(index_str)
    except ValueError:
        await callback.answer("❌ فرمت انتخاب نامعتبر است.")
        return

    data = await state.get_data()
    suggestions = data.get("last_suggestions", [])

    logger.info("🧩 Callback Data: %s", callback.data)
    logger.info("📋 Suggestions: %s", suggestions)
    logger.info("🔢 Index: %s", index)

    if not suggestions:
        await callback.answer("❌ لیست پیشنهادات یافت نشد. لطفاً دوباره تلاش کنید.")
        return

    if index >= len(suggestions):
        await callback.answer("❌ انتخاب نامعتبر است.")
        return

    selected_name = suggestions[index]

    await update_item_and_ask_for_weight(state, selected_name, callback.message)
    await callback.answer()

# ثبت نام قلم و پرسش وزن
async def update_item_and_ask_for_weight(state: FSMContext, item_name: str, message: types.Message):
    data = await state.get_data()
    index = data.get("current_index", 0)
    items = data.get("items", [])

    if len(items) <= index:
        items.append({})

    items[index]["name"] = item_name
    await state.update_data(items=items)
    await message.answer(f"⚖️ وزن قلم '{item_name}' را وارد کنید:")
    await state.set_state(ProductReportForm.waiting_for_each_item_weight)

# ثبت وزن قلم و رفتن به قلم بعدی یا گزارش نهایی
@dp.message(ProductReportForm.waiting_for_each_item_weight)
async def process_each_item_weight(message: types.Message, state: FSMContext):
    try:
        weight = float(message.text.strip())
        data = await state.get_data()
        items = data.get("items", [])
        items[-1]["weight"] = weight

        current_index = data.get("current_index", 0) + 1
        total_count = data.get("item_count", 1)
        await state.update_data(items=items, current_index=current_index)

        if current_index < total_count:
            await message.answer(f"📝 نام قلم بعدی ({current_index + 1}) را وارد کنید:")
            await state.set_state(ProductReportForm.waiting_for_each_item_name)
        else:
            await generate_production_report(message, state)
            await state.clear()
    except:
        await message.answer("❌ لطفاً یک عدد معتبر وارد کنید.")

# ساخت گزارش نهایی
async def generate_production_report(message: types.Message, state: FSMContext):
    data = await state.get_data()
    product_name = data.get("product_name")
    items = data.get("items", [])
    item_count = len(items)
    total_weight = sum(item.get("weight", 0) for item in items)
    user_data = await state.get_data()

    report = (
        f"\U0001F4CB **گزارش تولید کالا**\n"
        f"📅 تاریخ و ساعت: {jdatetime.datetime.now().strftime('%Y/%m/%d %H:%M')}\n"
        f"👤 نام کاربر: {user_data.get('user_name', 'نامشخص')}\n"
        f"📦 نام کالای تولیدی: {product_name}\n"
        f"🔢 تعداد اقلام: {item_count} عدد\n"
        f"------------------------------\n"
    )
    for i, item in enumerate(items, start=1):
        report += f"{i}. {item['name']} - {item['weight']} کیلوگرم\n"
    report += f"------------------------------\n"
    report += f"⚖️ وزن نهایی کل: {total_weight} کیلوگرم"

    await message.answer(report)
    await send_product_report_to_group(report)

# ارسال گزارش به تاپیک مربوطه در گروه
async def send_product_report_to_group(report_message):
    GROUP_ID = "-1002287304966"  # آیدی گروه
    THREAD_ID = 2644  # آیدی تاپیک گزارش تولید کالا

    try:
        await bot.send_message(
            chat_id=GROUP_ID,
            message_thread_id=THREAD_ID,
            text=report_message
        )
        print("✅ گزارش تولید کالا با موفقیت ارسال شد.")
    except Exception as e:
        print(f"❌ خطا در ارسال گزارش تولید کالا: {e}")

async def main():
    # مرحله اول: کش کالاها را بارگذاری کن
    refresh_products()

    # مرحله دوم: هر ۵ دقیقه کالاها را به‌روز نگه‌دار
    asyncio.create_task(auto_refresh_products())

    # حذف webhook قدیمی (مخصوص aiogram 3)
    await bot.delete_webhook(drop_pending_updates=True)

    # شروع ربات
    await dp.start_polling(bot)


# این باید دقیقا همین شکلی باشه:
if __name__== "__main__":
    import asyncio
    asyncio.run(main())