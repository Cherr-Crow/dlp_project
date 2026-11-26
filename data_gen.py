import json
import random
from faker import Faker

fake = Faker("ru_RU")
random.seed(42)
NUM_SAMPLES = 500

def gen_passport():
    return f"{random.randint(1000, 9999)} {random.randint(100000, 999999)}"

def gen_snils():
    return f"{random.randint(100,999)}-{random.randint(100,999)}-{random.randint(100,999)} {random.randint(10,99)}"

def gen_inn():
    n = random.choice([10, 12])
    return "".join(str(random.randint(0, 9)) for _ in range(n))

def gen_phone():
    return fake.phone_number()

def gen_fio():
    return fake.name()

def gen_address():
    return fake.address().replace("\n", ", ")

def gen_card():
    return f"{random.randint(4000, 4999)} {random.randint(1000, 9999)} {random.randint(1000, 9999)} {random.randint(1000, 9999)}"

def gen_email():
    return fake.email()

def gen_secret_amount():
    return f"{random.randint(10, 9999)} {random.choice(['руб', 'рублей', 'тыс. руб'])}"

PII_TEMPLATES = [
    ("Мой паспорт {passport}", ["PASSPORT"]),
    ("СНИЛС сотрудника {snils}", ["SNILS"]),
    ("ИНН клиента {inn}", ["INN"]),
    ("Позвоните мне на {phone}", ["PHONE"]),
    ("Клиент {fio} просит перезвонить", ["PERSON"]),
    ("Адрес доставки: {address}", ["ADDRESS"]),
    ("Карта для оплаты: {card}", ["BANK_CARD"]),
    ("Почта для связи: {email}", ["EMAIL"]),
    ("ФИО: {fio}, паспорт {passport}, СНИЛС {snils}", ["PERSON", "PASSPORT", "SNILS"]),
]

SECRET_TEMPLATES = [
    ("Себестоимость партии: {amount}", ["FINANCIAL_DATA"]),
    ("Прибыль за квартал составила {amount}", ["FINANCIAL_DATA"]),
    ("Маржинальность продукта {amount}", ["FINANCIAL_DATA"]),
    ("Это коммерческая тайна, {amount}", ["NDA_MARKER", "FINANCIAL_DATA"]),
    ("Пароль от wi-fi: {password}", ["SECRET"]),
    ("Токен доступа: sk-{password}", ["SECRET"]),
]

CLEAN_TEMPLATES = [
    "Добрый день, подскажите, пожалуйста, режим работы офиса.",
    "Какой у вас адрес электронной почты для заявок?",
    "Нужна консультация по тарифам на обслуживание.",
    "Спасибо, вопрос решён, до свидания.",
    "Уточните, работает ли офис в субботу.",
]

def make_pii_sample():
    tmpl, types = random.choice(PII_TEMPLATES)
    values = {
        "passport": gen_passport(), "snils": gen_snils(), "inn": gen_inn(),
        "phone": gen_phone(), "fio": gen_fio(), "address": gen_address(),
        "card": gen_card(), "email": gen_email()
    }
    text = tmpl.format(**values)
    entities = []
    for t in types:
        key = {"PASSPORT": "passport", "SNILS": "snils", "INN": "inn", "PHONE": "phone", 
               "PERSON": "fio", "ADDRESS": "address", "BANK_CARD": "card", "EMAIL": "email"}[t]
        entities.append({"type": t, "text": values[key]})
    return {"text": text, "label": 1, "entities": entities}

def make_secret_sample():
    tmpl, types = random.choice(SECRET_TEMPLATES)
    vals = {"amount": gen_secret_amount(), "password": fake.password(length=10)}
    text = tmpl.format(**vals)
    entities = []
    for t in types:
        if t == "FINANCIAL_DATA":
            entities.append({"type": t, "text": vals["amount"]})
        elif t == "SECRET":
            entities.append({"type": t, "text": vals["password"]})
        else:
            entities.append({"type": t, "text": "коммерческая тайна"})
    return {"text": text, "label": 1, "entities": entities}

def make_clean_sample():
    return {"text": random.choice(CLEAN_TEMPLATES), "label": 0, "entities": []}

def build_dataset(n):
    data = []
    for _ in range(n):
        r = random.random()
        if r < 0.50: data.append(make_pii_sample())
        elif r < 0.80: data.append(make_secret_sample())
        else: data.append(make_clean_sample())
    random.shuffle(data)
    return data

if __name__ == "__main__":
    dataset = build_dataset(NUM_SAMPLES)
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    print(f"Успех! Сгенерировано {len(dataset)} записей в data.json")