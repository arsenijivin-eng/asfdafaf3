import asyncio, os, sqlite3, random
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

TOKEN = os.getenv('BOT_TOKEN', '')
ADMIN_ID = 7894051808
CHANNEL = '@hoqanft'
VPN_URL = 'https://t.me/CristyVPN_bot?start=7894051808'
APPLY_URL = 'https://t.me/+IxVXx6qkPEpjZTYy'
COMMENT_TEXT = '@hoqabot спс за букет 💐'
NFT_LINK = 'https://t.me/nft/SnoopCigar-36783'
DB = str(BASE_DIR / 'hoqabot.db')
IMG = str(BASE_DIR / 'images')

if not TOKEN:
    raise RuntimeError('BOT_TOKEN is not set')
bot = Bot(TOKEN)
dp = Dispatcher()

# Простые задания после подписок. Можно легко расширять этот список.
QUIZ_POOL = [
    ('Какого цвета обычно трава?', ['Синего', 'Зелёного', 'Красного', 'Фиолетового'], 1),
    ('Сколько будет 2 + 5?', ['6', '7', '8', '9'], 1),
    ('Какое животное говорит «му»?', ['Кошка', 'Собака', 'Корова', 'Лошадь'], 2),
    ('Что обычно нельзя съесть: грушу или камень?', ['Грушу', 'Камень'], 1),
    ('Сколько дней в неделе?', ['5', '6', '7', '8'], 2),
    ('Сколько будет 10 - 3?', ['6', '7', '8', '9'], 1),
    ('Какое животное говорит «мяу»?', ['Кошка', 'Корова', 'Лошадь', 'Курица'], 0),
    ('Сколько ног у обычной собаки?', ['2', '4', '6', '8'], 1),
    ('Какой фрукт обычно жёлтый?', ['Банан', 'Огурец', 'Картофель', 'Морковь'], 0),
    ('Что светит днём на небе?', ['Луна', 'Солнце', 'Фонарик', 'Звезда'], 1),
    ('Сколько будет 3 + 4?', ['5', '6', '7', '8'], 2),
    ('Какое животное говорит «гав»?', ['Кошка', 'Собака', 'Корова', 'Утка'], 1),
    ('Какой формы обычно мяч?', ['Круглой', 'Квадратной', 'Треугольной', 'Прямоугольной'], 0),
    ('Что обычно растёт на дереве?', ['Яблоко', 'Телефон', 'Мяч', 'Книга'], 0),
    ('Сколько месяцев в году?', ['10', '11', '12', '13'], 2),
    ('Какой напиток обычно делают из воды и чайных листьев?', ['Чай', 'Кетчуп', 'Суп', 'Молоко'], 0),
    ('Что из этого умеет летать?', ['Самолёт', 'Стол', 'Стул', 'Кровать'], 0),
    ('Какое время суток бывает после дня?', ['Утро', 'Ночь', 'Полдень', 'Завтрак'], 1),
    ('Сколько будет 5 + 5?', ['8', '9', '10', '11'], 2),
    ('Какой цвет получается при смешении синего и жёлтого?', ['Зелёный', 'Красный', 'Розовый', 'Чёрный'], 0),
]
QUIZ_COUNT = 10


def db():
    con = sqlite3.connect(DB)
    con.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, first_seen TEXT, last_seen TEXT)')
    con.execute('CREATE TABLE IF NOT EXISTS actions (user_id INTEGER, action TEXT, ts TEXT)')
    con.execute('CREATE TABLE IF NOT EXISTS comment_progress (user_id INTEGER PRIMARY KEY, photos INTEGER DEFAULT 0)')
    con.execute('CREATE TABLE IF NOT EXISTS mid_comment_progress (user_id INTEGER PRIMARY KEY, photos INTEGER DEFAULT 0)')
    con.execute('CREATE TABLE IF NOT EXISTS subscriptions (id INTEGER PRIMARY KEY AUTOINCREMENT, chat TEXT UNIQUE NOT NULL, title TEXT NOT NULL, url TEXT NOT NULL)')
    con.execute('CREATE TABLE IF NOT EXISTS quiz_progress (user_id INTEGER PRIMARY KEY, question_ids TEXT NOT NULL, position INTEGER DEFAULT 0)')
    con.commit()
    return con


def seed_subscriptions():
    con = db()
    con.execute('INSERT OR IGNORE INTO subscriptions(chat,title,url) VALUES(?,?,?)', (CHANNEL, 'Подпишись на канал', 'https://t.me/hoqanft'))
    con.commit(); con.close()

seed_subscriptions()


def touch_user(user):
    con = db(); now = datetime.now(timezone.utc).isoformat()
    con.execute('INSERT INTO users VALUES(?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET username=excluded.username,last_seen=excluded.last_seen', (user.id, user.username or '', now, now))
    con.commit(); con.close()


def action(uid, name):
    con = db(); con.execute('INSERT INTO actions VALUES(?,?,?)', (uid, name, datetime.now(timezone.utc).isoformat())); con.commit(); con.close()


def get_subscriptions():
    con = db(); rows = con.execute('SELECT id,chat,title,url FROM subscriptions ORDER BY id').fetchall(); con.close(); return rows


def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='⚽ Удар по воротам', callback_data='game:football'), InlineKeyboardButton(text='🏀 Бросок в кольцо', callback_data='game:basketball')]])


def reward_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🎁 Посмотреть NFT', callback_data='nft:view')]])


def nft_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🔗 Открыть NFT', url=NFT_LINK)], [InlineKeyboardButton(text='🎁 Забрать NFT', callback_data='nft:claim')]])


def comments_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='💬 Перейти к комментариям', callback_data='tasks:comments')]])


def mid_comments_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='💬 Выполнить задание', callback_data='tasks:mid_comments')]])


def tasks_kb():
    rows = []
    for i, (_, chat, title, url) in enumerate(get_subscriptions(), 1):
        rows.append([InlineKeyboardButton(text=f'{i}️⃣ {title}', url=url)])
    rows += [
        [InlineKeyboardButton(text='🌐 Лучший VPN', url=VPN_URL)],
        [InlineKeyboardButton(text='📝 Подать заявку', url=APPLY_URL)],
        [InlineKeyboardButton(text='✅ Проверить подписки', callback_data='tasks:check')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def quiz_answer_kb(options):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f'{chr(65+i)}) {option}', callback_data=f'quiz:answer:{i}') for i, option in enumerate(options[:2])],
        [InlineKeyboardButton(text=f'{chr(65+i)}) {option}', callback_data=f'quiz:answer:{i}') for i, option in enumerate(options[2:], 2)]
    ])


def quiz_start(user_id):
    ids = random.sample(range(len(QUIZ_POOL)), min(QUIZ_COUNT, len(QUIZ_POOL)))
    con = db(); con.execute('INSERT INTO quiz_progress(user_id,question_ids,position) VALUES(?,?,0) ON CONFLICT(user_id) DO UPDATE SET question_ids=excluded.question_ids,position=0', (user_id, ','.join(map(str, ids)))); con.commit(); con.close()
    return ids


def get_quiz_state(user_id):
    con = db(); row = con.execute('SELECT question_ids,position FROM quiz_progress WHERE user_id=?', (user_id,)).fetchone(); con.close()
    if not row: return None
    ids = [int(x) for x in row[0].split(',') if x]
    return ids, row[1]


@dp.message(CommandStart())
async def start(message: Message):
    touch_user(message.from_user)
    await message.answer_photo(FSInputFile(f'{IMG}/start.jpg'), caption='Испытайте удачу!\n\nВыберите, ударить по воротам или бросить мяч в кольцо, чтобы получить приз ⚽🏀', reply_markup=main_kb())


@dp.callback_query(F.data.startswith('game:'))
async def game(call: CallbackQuery):
    touch_user(call.from_user)
    sport = call.data.split(':', 1)[1]
    action(call.from_user.id, f'game_{sport}')
    gif = f'{IMG}/{sport}.gif'
    label = 'Удар по воротам' if sport == 'football' else 'Бросок в кольцо'
    await call.message.answer_animation(FSInputFile(gif), caption=f'{label} 🎯\n\n🎉 Вы попали!\n\nВам доступен NFT-приз. Выполните задания, чтобы получить его.', reply_markup=reward_kb())
    await call.answer()


@dp.callback_query(F.data == 'nft:view')
async def nft_view(call: CallbackQuery):
    touch_user(call.from_user); action(call.from_user.id, 'nft_view')
    await call.message.answer_photo(FSInputFile(f'{IMG}/nft.jpg'), caption=f'🎁 Ваш NFT\n\nСсылка на коллекционный подарок:\n{NFT_LINK}\n\nНажмите «Забрать NFT», чтобы перейти к первому обязательному заданию.', reply_markup=nft_kb())
    await call.answer()


@dp.callback_query(F.data == 'nft:claim')
async def nft_claim(call: CallbackQuery):
    touch_user(call.from_user); action(call.from_user.id, 'nft_claim')
    await call.message.answer_photo(FSInputFile(f'{IMG}/comments.jpg'), caption='💬 Первое задание\n\nОставьте 10 комментариев под видео о подарках или звёздах в TikTok.\n\nТекст комментария:\n' + COMMENT_TEXT + '\n\nПоставьте лайк каждому комментарию и отправьте боту 10 скриншотов.\n\nПосле 10 скриншотов откроются задания.', reply_markup=comments_kb())
    await call.answer()


@dp.callback_query(F.data == 'tasks:open')
async def tasks_open(call: CallbackQuery):
    state = get_quiz_state(call.from_user.id)
    if state and state[1] == 5:
        await call.message.answer_photo(FSInputFile(f'{IMG}/comments.jpg'), caption='💬 Сначала выполните дополнительное задание\n\nОставьте 10 комментариев под видео в TikTok (это не задание на NFT).\n\nТекст:\n@hoqabot спасибо за задание ❤️\n\nПоставьте лайк каждому комментарию и отправьте 10 скриншотов боту.\nПосле этого продолжится вопрос 6.', reply_markup=mid_comments_kb()); await call.answer(); return
    await call.message.answer_photo(FSInputFile(f'{IMG}/tasks.jpg'), caption='Отлично! Комментарии выполнены. Теперь доступны подписки и другие задания.\n\nПосле выполнения подписок нажмите «✅ Проверить подписки».', reply_markup=tasks_kb()); await call.answer()


@dp.callback_query(F.data == 'tasks:comments')
async def comments_task(call: CallbackQuery):
    touch_user(call.from_user); action(call.from_user.id, 'comments_task')
    await call.message.answer_photo(FSInputFile(f'{IMG}/comments.jpg'), caption='Задание 2\n\nОставьте 10 комментариев под видео о подарках или звёздах в TikTok.\n\nТекст:\n' + COMMENT_TEXT + '\n\nПоставьте лайк каждому комментарию.\nОтправьте боту 10 скриншотов выполненного задания.', reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='⬅️ К заданиям', callback_data='tasks:open')]])); await call.answer()


@dp.callback_query(F.data == 'tasks:mid_comments')
async def mid_comments_task(call: CallbackQuery):
    touch_user(call.from_user); action(call.from_user.id, 'mid_comments_task')
    await call.message.answer_photo(FSInputFile(f'{IMG}/comments.jpg'), caption='💬 Дополнительное задание\n\nОставьте 10 комментариев под видео в TikTok. Это НЕ задание на NFT.\n\nТекст комментария:\n@hoqabot спасибо за задание ❤️\n\nПоставьте лайк каждому комментарию.\nОтправьте боту 10 скриншотов выполненного задания.\n\nПосле этого продолжится 6-й вопрос.', reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='⬅️ К заданиям', callback_data='tasks:open')]])); await call.answer()


@dp.message(F.photo)
async def screenshots(message: Message):
    touch_user(message.from_user)
    state = get_quiz_state(message.from_user.id)
    # Если пользователь сейчас проходит промежуточное задание после 5-го вопроса.
    if state:
        ids, pos = state
        if pos == 5:
            con = db(); row = con.execute('SELECT photos FROM mid_comment_progress WHERE user_id=?', (message.from_user.id,)).fetchone(); count = (row[0] if row else 0) + 1
            con.execute('INSERT INTO mid_comment_progress(user_id,photos) VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET photos=excluded.photos', (message.from_user.id, count)); con.commit(); con.close()
            if count < 10:
                await message.answer(f'📸 Скриншот дополнительного задания {count}/10 принят.')
            else:
                action(message.from_user.id, 'mid_comments_10_screenshots')
                nq = QUIZ_POOL[ids[pos]]
                await message.answer(f'✅ 10 скриншотов получено!\n\nПродолжаем. Вопрос 6/{len(ids)}\n{nq[0]}', reply_markup=quiz_answer_kb(nq[1]))
            return

    # Первое задание с комментариями после NFT.
    con = db(); row = con.execute('SELECT photos FROM comment_progress WHERE user_id=?', (message.from_user.id,)).fetchone(); count = (row[0] if row else 0) + 1
    con.execute('INSERT INTO comment_progress(user_id,photos) VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET photos=excluded.photos', (message.from_user.id, count)); con.commit(); con.close()
    if count < 10:
        await message.answer(f'📸 Скриншот {count}/10 принят.')
    else:
        action(message.from_user.id, 'comments_10_screenshots'); await message.answer_photo(FSInputFile(f'{IMG}/tasks.jpg'), caption='✅ 10 скриншотов получено!\n\nТеперь доступны подписки и задания. Выполните их и нажмите «Проверить подписки».', reply_markup=tasks_kb())


async def check_subscriptions(user_id):
    failed = []
    for sid, chat, title, url in get_subscriptions():
        try:
            member = await bot.get_chat_member(chat, user_id)
            if member.status not in {'member', 'administrator', 'creator'}:
                failed.append(title)
        except Exception:
            failed.append(title)
    return failed


@dp.callback_query(F.data == 'tasks:check')
async def tasks_check(call: CallbackQuery):
    touch_user(call.from_user)
    photos = (db().execute('SELECT photos FROM comment_progress WHERE user_id=?', (call.from_user.id,)).fetchone() or [0])[0]
    if photos < 10:
        await call.answer(f'Нужно отправить ещё {10-photos} скриншотов.', show_alert=True); return
    failed = await check_subscriptions(call.from_user.id)
    if failed:
        await call.answer('Не выполнено: ' + ', '.join(failed), show_alert=True); return
    action(call.from_user.id, 'subscriptions_verified')
    ids = quiz_start(call.from_user.id)
    q = QUIZ_POOL[ids[0]]
    await call.message.answer(f'✅ Подписки проверены!\n\nТеперь лёгкие задания. Всего будет {len(ids)} вопросов.\n\nВопрос 1/{len(ids)}\n{q[0]}', reply_markup=quiz_answer_kb(q[1]))
    await call.answer()


@dp.callback_query(F.data.startswith('quiz:answer:'))
async def quiz_answer(call: CallbackQuery):
    state = get_quiz_state(call.from_user.id)
    if not state:
        await call.answer('Сначала пройди подписки.', show_alert=True); return
    ids, pos = state
    if pos >= len(ids):
        await call.answer('Тест уже завершён.', show_alert=True); return
    answer = int(call.data.rsplit(':', 1)[1])
    q = QUIZ_POOL[ids[pos]]
    if answer != q[2]:
        await call.answer('❌ Неверно. Попробуй ещё раз.', show_alert=True); return
    pos += 1
    con = db(); con.execute('UPDATE quiz_progress SET position=? WHERE user_id=?', (pos, call.from_user.id)); con.commit(); con.close()
    if pos >= len(ids):
        action(call.from_user.id, 'quiz_completed')
        await call.message.answer_photo(FSInputFile(f'{IMG}/nft.jpg'), caption='🎉 Все лёгкие задания выполнены!\n\nСпасибо. Ожидайте выдачи NFT.')
        await call.answer('✅ Всё правильно!')
        return
    # После 5-го вопроса вставляем отдельное задание на 10 комментариев.
    if pos == 5:
        con = db(); con.execute('INSERT INTO mid_comment_progress(user_id,photos) VALUES(?,0) ON CONFLICT(user_id) DO UPDATE SET photos=0', (call.from_user.id,)); con.commit(); con.close()
        await call.message.answer_photo(FSInputFile(f'{IMG}/comments.jpg'), caption='💬 Дополнительное задание\n\nОставьте 10 комментариев под любыми подходящими видео в TikTok. Это отдельное задание, не связанное с NFT.\n\nТекст комментария:\n@hoqabot спасибо за задание ❤️\n\nПоставьте лайк каждому комментарию и отправьте боту 10 скриншотов выполненного задания.\n\nПосле 10 скриншотов продолжится вопрос 6.', reply_markup=mid_comments_kb())
        await call.answer('✅ 5 вопросов выполнено!')
        return
    nq = QUIZ_POOL[ids[pos]]
    await call.message.edit_text(f'✅ Правильно!\n\nВопрос {pos+1}/{len(ids)}\n{nq[0]}', reply_markup=quiz_answer_kb(nq[1]))
    await call.answer('✅ Правильно!')


@dp.message(Command('admin'))
async def admin(message: Message):
    if message.from_user.id != ADMIN_ID: return
    con = db(); total = con.execute('SELECT COUNT(*) FROM users').fetchone()[0]; today = datetime.now(timezone.utc).date().isoformat(); today_count = con.execute('SELECT COUNT(*) FROM users WHERE substr(first_seen,1,10)=?', (today,)).fetchone()[0]; actions = con.execute('SELECT COUNT(*) FROM actions').fetchone()[0]; con.close()
    subs = get_subscriptions()
    sub_text = '\n'.join(f'{i}. {r[2]} — {r[1]}' for i, r in enumerate(subs, 1)) or 'нет'
    await message.answer(f'🛠 Админка\n\nПользователей всего: {total}\nНовых сегодня: {today_count}\nДействий всего: {actions}\n\n📌 Задания-подписки:\n{sub_text}\n\nКоманды:\n/addsub @канал Название — добавить подписку\n/delsub ID — удалить подписку\n/subs — список подписок\n/broadcast текст — рассылка')


@dp.message(Command('subs'))
async def subs(message: Message):
    if message.from_user.id != ADMIN_ID: return
    rows = get_subscriptions()
    if not rows: return await message.answer('Заданий-подписок нет.')
    await message.answer('📌 Задания-подписки:\n\n' + '\n'.join(f'ID {r[0]} — {r[2]} ({r[1]})' for r in rows))


@dp.message(Command('addsub'))
async def addsub(message: Message):
    if message.from_user.id != ADMIN_ID: return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3 or not parts[1].startswith('@'):
        return await message.answer('Использование:\n/addsub @username Название задания')
    chat, title = parts[1], parts[2].strip()
    url = f'https://t.me/{chat[1:]}'
    con = db()
    try:
        con.execute('INSERT INTO subscriptions(chat,title,url) VALUES(?,?,?)', (chat, title, url)); con.commit()
        await message.answer(f'✅ Добавлено:\n{title}\n{chat}')
    except sqlite3.IntegrityError:
        await message.answer('⚠️ Такая подписка уже есть.')
    finally:
        con.close()


@dp.message(Command('delsub'))
async def delsub(message: Message):
    if message.from_user.id != ADMIN_ID: return
    parts = message.text.split(maxsplit=1)
    if len(parts) != 2 or not parts[1].isdigit():
        return await message.answer('Использование: /delsub ID')
    con = db(); cur = con.execute('DELETE FROM subscriptions WHERE id=?', (int(parts[1]),)); con.commit(); con.close()
    await message.answer('✅ Удалено.' if cur.rowcount else '❌ ID не найден.')


@dp.message(Command('broadcast'))
async def broadcast(message: Message):
    if message.from_user.id != ADMIN_ID: return
    text = message.text.partition(' ')[2].strip()
    if not text: return await message.answer('Использование: /broadcast текст')
    con = db(); ids = [r[0] for r in con.execute('SELECT user_id FROM users')]; con.close(); sent = 0
    for uid in ids:
        try: await bot.send_message(uid, text); sent += 1; await asyncio.sleep(.04)
        except Exception: pass
    await message.answer(f'Рассылка завершена: {sent}/{len(ids)}')


async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
