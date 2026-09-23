"""One-shot generator for the sealed v17 holdout. Do not rerun after sealing."""

import hashlib
import json
from pathlib import Path

OUT = Path(__file__).with_name("sealed_holdout_v17.json")
cases = []


def add(text, pairs, focus, tags):
    entities, cursor = [], 0
    for typ, value in pairs:
        start = text.find(value, cursor)
        if start < 0:
            raise ValueError((typ, value, text))
        entities.append({"type": typ, "value": value, "start": start, "end": start + len(value)})
        cursor = start + len(value)
    cases.append(
        {
            "id": f"v17-{len(cases) + 1:04d}",
            "text": text,
            "expected_entities": entities,
            "focus": focus,
            "tags": tags,
        }
    )


def inn10(n):
    a = [int(x) for x in f"{770000000 + n:09d}"]
    return "".join(map(str, a)) + str(
        sum(x * y for x, y in zip(a, [2, 4, 10, 3, 5, 9, 4, 6, 8], strict=True))
        % 11
        % 10
    )


def luhn(seed):
    s = ("2204" + f"{seed:011d}")[:15]
    total = 0
    for i, c in enumerate(s):
        d = int(c) * (2 if i % 2 == 0 else 1)
        total += d - 9 if d > 9 else d
    return s + str((-total) % 10)


first = ["Агата", "Тимофей", "Элина", "Марат", "Яна", "Родион", "Лилия", "Феликс", "Нелли", "Глеб"]
middle = [
    "Романовна",
    "Львович",
    "Савельевна",
    "Ильич",
    "Платоновна",
    "Эдуардович",
    "Аркадьевна",
    "Олегович",
    "Яковлевна",
    "Русланович",
]
last = [
    "Белова",
    "Горин",
    "Дроздова",
    "Ефремов",
    "Журавлёва",
    "Зимин",
    "Иволгина",
    "Котов",
    "Лапина",
    "Мельников",
]
names = [f"{first[i]} {middle[i]} {last[i]}" for i in range(10)]
cities = [
    "Архангельск",
    "Самара",
    "Казань",
    "Пермь",
    "Красноярск",
    "Омск",
    "Новосибирск",
    "Ноябрьск",
    "Ростов-на-Дону",
    "Краснодар",
]
regions = [
    "Архангельской области",
    "Самарской области",
    "Республики Татарстан",
    "Пермского края",
    "Красноярского края",
    "Омской области",
    "Новосибирской области",
    "ЯНАО",
    "Ростовской области",
    "Краснодарского края",
]
streets0 = [
    "Воскресенская",
    "Московское шоссе",
    "Баумана",
    "Ленина",
    "Мира",
    "Щербанёва",
    "Депутатская",
    "Советская",
    "Пушкинская",
    "Красная",
]
post = [
    "163071",
    "443086",
    "420111",
    "614000",
    "660049",
    "644024",
    "630099",
    "629807",
    "344006",
    "350000",
]
country = [
    "Россия",
    "Беларусь",
    "Казахстан",
    "Армения",
    "Кыргызстан",
    "Узбекистан",
    "Таджикистан",
    "Азербайджан",
    "Молдова",
    "Монголия",
]
dates = [
    "17.02.1987",
    "1989-11-23",
    "04/08/1993",
    "1 марта 1976 года",
    "07\u00a0мая\u00a01991",
    "1998.14.09",
    "29-12-1968",
    "третьего июня 1984 г.",
    "10.10.2001",
    "2000/31/01",
]
issue_dates = [
    "12.06.2015",
    "2018-03-27",
    "09/11/2020",
    "22 января 2014 года",
    "04\u00a0августа\u00a02019",
    "2012.15.10",
    "31-05-2017",
    "7 февраля 2021 г.",
    "19.12.2016",
    "2022/08/30",
]
birthplaces = [f"город {cities[i]} {regions[i]}" for i in range(10)]
passports = [f"{40 + i:02d} {11 + i:02d} {816204 + i * 7319:06d}" for i in range(10)]
passports[1] = "серия 52 19 номер 304781"
passports[2] = "40\u00a018\u00a0672391"
passports[4] = "серия\u00a03208 №\u00a0571462"
issuers = [f"ОВМ УМВД России по {regions[i]}" for i in range(10)]
dept = [f"{210 + i * 37:03d}-{(184 + i * 23) % 1000:03d}" for i in range(10)]
dept[1] = dept[1].replace("-", "\u2011")
dept[4] = dept[4].replace("-", "—")
dept[7] = dept[7].replace("-", " ")
licenses = [
    f"{50 + i:02d} {chr(1040 + i)}{chr(1050 + i)} {826305 + i * 9257:06d}" for i in range(10)
]
houses = [f"дом {n}" for n in [91, 33, 52, 68, 42, 18, 27, 74, 101, 88]]
houses[1] = "д. 33Б"
houses[4] = "владение 42"
apart = [f"квартира {n}" for n in [24, 117, 14, 9, 81, 6, 53, 10, 35, 12]]
apart[2] = "кв\u00a014"
apart[3] = "квартира № 9"
streets = [("проспект " if i == 4 else "улица ") + x for i, x in enumerate(streets0)]
addresses = [
    f"Россия, {post[i]}, г. {cities[i]}, {streets[i]}, {houses[i]}, {apart[i]}" for i in range(10)
]
emails = [
    f"{first[i].lower()}.{last[i].lower().replace('ё', 'e')}+v17@client-{i + 31}.example"
    for i in range(10)
]
phones = [f"+7 ({901 + i * 2}) {318 + i * 17:03d}-{24 + i:02d}-{51 - i:02d}" for i in range(10)]
phones[2] = phones[2].replace(" ", "\u00a0").replace("-", "\u2011")
phones[7] = phones[7].replace("-", " ")
inns = [inn10(1739 + i * 7919) for i in range(10)]
cards0 = [luhn(73190428651 + i * 9271) for i in range(10)]
cards = [
    " ".join(x[j : j + 4] for j in range(0, 16, 4))
    if i % 3 == 0
    else ("-".join(x[j : j + 4] for j in range(0, 16, 4)) if i % 3 == 1 else x)
    for i, x in enumerate(cards0)
]
cvv = ["184", "027", "615", "903", "442", "708", "356", "091", "827", "530"]
pins = ["1846", "0275", "6159", "9031", "4428", "7083", "3560", "0917", "8274", "5302"]
holders = [f"{first[i].upper()} {last[i].upper().replace('Ё', 'E')}" for i in range(10)]

specs = [
    ("full_name", names, "ФИО клиента"),
    ("date_of_birth", dates, "Дата рождения"),
    ("place_of_birth", birthplaces, "Место рождения"),
    ("passport", passports, "Паспорт клиента"),
    ("citizenship", country, "Гражданство клиента"),
    ("passport_issuer", issuers, "Паспорт выдан"),
    ("department_code", dept, "Код подразделения"),
    ("passport_issue_date", issue_dates, "Дата выдачи паспорта"),
    ("driver_license", licenses, "Водительское удостоверение"),
    ("address", addresses, "Адрес регистрации"),
    ("country", country, "Страна проживания клиента"),
    ("postal_code", post, "Почтовый индекс получателя"),
    ("city", cities, "Город проживания клиента"),
    ("street", streets, "Улица регистрации"),
    ("house", houses, "Дом клиента"),
    ("apartment", apart, "Квартира клиента"),
    ("email", emails, "Email клиента"),
    ("phone", phones, "Телефон клиента"),
    ("inn", inns, "ИНН клиента"),
    ("bank_card", cards, "Номер карты клиента"),
    ("cvv", cvv, "CVV карты клиента"),
    ("pin", pins, "ПИН-код карты клиента"),
    ("cardholder_name", holders, "Имя держателя карты"),
]
templates = ["{}: {}.", "В анкете поле «{}» содержит {}.", 'profile["{}"]="{}"', "{} — {}."]
for typ, vals, label in specs:
    for i, val in enumerate(vals):
        text = templates[i % 4].format(label, val)
        tags = ["single", "russian", "technical" if i % 4 == 2 else "natural"]
        if i in (2, 4, 7):
            tags.append("ocr_unicode")
        if typ in {"bank_card", "cvv", "pin", "cardholder_name"}:
            tags.append("financial")
        add(text, [(typ, val)], typ, tags)

neg = [
    "Александр Сергеевич Пушкин родился в Москве в 1799 году.",
    "Роман «Война и мир» написал Лев Николаевич Толстой.",
    "Юрий Гагарин совершил первый космический полёт 12 апреля 1961 года.",
    "Таблица Менделеева названа в честь Дмитрия Ивановича Менделеева.",
    "Пётр Чайковский — автор балета «Щелкунчик».",
    "Адрес Эрмитажа: Дворцовая площадь, 2 — публичная справочная информация.",
    "Главный корпус МГУ расположен по адресу Ленинские горы, дом 1.",
    "Почтовый индекс 101000 относится к нескольким отделениям в центре Москвы.",
    "Телефон 112 используется для вызова экстренных служб.",
    "На странице документации приведён пример user@example.com.",
    "Версия сборки 7.921.418.63.27 не является телефонным номером.",
    "Ошибка HTTP 401 означает, что запрос не аутентифицирован.",
    "Параметр timeout=443086 задаёт число микросекунд, а не индекс.",
    "Значение trace_id=7701000000 служит техническим идентификатором.",
    "Последовательность 2204 0731 9042 8651 — тестовый вектор, не реквизит клиента.",
    "В инструкции написано: «Введите четыре цифры ПИН-кода», самого кода здесь нет.",
    "Поле CVV должно содержать три цифры, но значение не передано.",
    "Слово «Россия» в названии книги не описывает гражданство человека.",
    "Краснодар победил в футбольном матче со счётом 2:1.",
    "Улица Красная перекрыта для городского фестиваля.",
    "Дом 2 считается памятником архитектуры регионального значения.",
    "Квартира № 50 — название советского мультфильма.",
    "Дата 2026-09-23 обозначает выпуск релиза приложения.",
    "Код подразделения в схеме API имеет тип string.",
    "Серия и номер паспорта обязательны при очной идентификации.",
    "Карты платёжной системы могут начинаться с цифр 2200.",
    "ИНН организации проверяется отдельным сервисом.",
    "Переменная cardholder_name пока равна null.",
    "Лог: email field omitted; phone field omitted; address field omitted.",
    "Москва — столица Российской Федерации.",
]
for i, text in enumerate(neg):
    add(
        text,
        [],
        "clean",
        ["clean_negative", "public_fact" if i < 10 or i in (17, 18, 19, 29) else "technical"],
    )

multi = [
    f"Клиент {names[0]}, дата рождения {dates[0]}, телефон {phones[0]}.",
    f"Анкета: {names[1]}; паспорт {passports[1]}; код подразделения {dept[1]}.",
    f"Отправить договор на {emails[2]}, адрес регистрации: {addresses[2]}.",
    f"Карта {cards[3]}, CVV {cvv[3]}, держатель {holders[3]}.",
    f"PAN={cards[4]}; PIN={pins[4]}; mobile={phones[4]}",
    f"{names[5]} родился в месте: {birthplaces[5]}; гражданство: {country[5]}.",
    f"ВУ {licenses[6]} принадлежит клиенту {names[6]}, ИНН {inns[6]}.",
    f"Паспорт {passports[7]} выдан {issuers[7]} {issue_dates[7]}.",
    f"Получатель {names[8]}; email {emails[8]}; тел. {phones[8]}.",
    (
        f"Регистрация: страна {country[9]}, индекс {post[9]}, город {cities[9]}, "
        f"{streets[9]}, {houses[9]}, {apart[9]}."
    ),
    f"ФИО={names[2]}; email={emails[2]}; inn={inns[2]}",
    f"Заявитель {names[3]} сообщил карту {cards[3]} и код с оборота {cvv[3]}.",
    f"Дата рождения {dates[4]}; паспорт выдан {issue_dates[4]}; орган: {issuers[4]}.",
    f"Контакт {phones[5]}, почта {emails[5]}, проживание: {addresses[5]}.",
    f"card=pan:{cards[6]},pin:{pins[6]},holder:{holders[6]}",
    f"ФИО {names[7]}; место рождения {birthplaces[7]}; ВУ {licenses[7]}.",
    f"Документ {passports[8]}, дата выдачи {issue_dates[8]}, код {dept[8]}.",
    f"Налогоплательщик {names[9]}: ИНН {inns[9]}, гражданство {country[9]}.",
    f"Получатель карты {holders[0]}; номер {cards[0]}; CVV {cvv[0]}; PIN {pins[0]}.",
    f"Адрес: {post[1]}, {cities[1]}, {streets[1]}, {houses[1]}, {apart[1]}; телефон {phones[1]}.",
]
mpairs = [
    [("full_name", names[0]), ("date_of_birth", dates[0]), ("phone", phones[0])],
    [("full_name", names[1]), ("passport", passports[1]), ("department_code", dept[1])],
    [("email", emails[2]), ("address", addresses[2])],
    [("bank_card", cards[3]), ("cvv", cvv[3]), ("cardholder_name", holders[3])],
    [("bank_card", cards[4]), ("pin", pins[4]), ("phone", phones[4])],
    [("full_name", names[5]), ("place_of_birth", birthplaces[5]), ("citizenship", country[5])],
    [("driver_license", licenses[6]), ("full_name", names[6]), ("inn", inns[6])],
    [
        ("passport", passports[7]),
        ("passport_issuer", issuers[7]),
        ("passport_issue_date", issue_dates[7]),
    ],
    [("full_name", names[8]), ("email", emails[8]), ("phone", phones[8])],
    [
        ("country", country[9]),
        ("postal_code", post[9]),
        ("city", cities[9]),
        ("street", streets[9]),
        ("house", houses[9]),
        ("apartment", apart[9]),
    ],
    [("full_name", names[2]), ("email", emails[2]), ("inn", inns[2])],
    [("full_name", names[3]), ("bank_card", cards[3]), ("cvv", cvv[3])],
    [
        ("date_of_birth", dates[4]),
        ("passport_issue_date", issue_dates[4]),
        ("passport_issuer", issuers[4]),
    ],
    [("phone", phones[5]), ("email", emails[5]), ("address", addresses[5])],
    [("bank_card", cards[6]), ("pin", pins[6]), ("cardholder_name", holders[6])],
    [("full_name", names[7]), ("place_of_birth", birthplaces[7]), ("driver_license", licenses[7])],
    [
        ("passport", passports[8]),
        ("passport_issue_date", issue_dates[8]),
        ("department_code", dept[8]),
    ],
    [("full_name", names[9]), ("inn", inns[9]), ("citizenship", country[9])],
    [("cardholder_name", holders[0]), ("bank_card", cards[0]), ("cvv", cvv[0]), ("pin", pins[0])],
    [
        ("postal_code", post[1]),
        ("city", cities[1]),
        ("street", streets[1]),
        ("house", houses[1]),
        ("apartment", apart[1]),
        ("phone", phones[1]),
    ],
]
for i, (text, pairs) in enumerate(zip(multi, mpairs, strict=True)):
    tags = ["multi_pii", "russian"]
    if i in (4, 10, 14):
        tags.append("technical")
    if "\u00a0" in text or "\u2011" in text or "—" in text:
        tags.append("ocr_unicode")
    if any(t in text for t in ("PAN=", "card=", "CVV", "карта")):
        tags.append("financial")
    add(text, pairs, "multi", tags)

payload = {
    "version": "17",
    "language": "ru",
    "purpose": "sealed blind holdout for PII masking evaluation",
    "requirements_sources": [
        "RAW/requirements.md",
        "database/chunks/CH-SRC-001-05.md",
        "database/chunks/CH-SRC-001-06.md",
        "database/chunks/CH-SRC-001-09.md",
        "database/chunks/CH-SRC-002-06.md",
        "database/chunks/CH-SRC-003-03.md",
        "database/chunks/CH-SRC-003-04.md",
    ],
    "entity_types": [x[0] for x in specs],
    "case_count": len(cases),
    "cases": cases,
}
OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
print(f"cases={len(cases)} sha256={digest} bytes={OUT.stat().st_size}")
