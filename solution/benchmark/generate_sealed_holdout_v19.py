"""Generate the deterministic blind v19 holdout without importing production code."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

OUT = Path(__file__).with_name("sealed_holdout_v19.json")

SURNAMES = [
    "Алфёров",
    "Бестужев",
    "Воронцов",
    "Громыко",
    "Демидов",
    "Елагин",
    "Жданов",
    "Зорин",
    "Ильин",
    "Калинин",
    "Лапшин",
    "Мельников",
    "Нестеров",
    "Овсянников",
    "Панфилов",
    "Рогожин",
    "Сафронов",
    "Тихонов",
    "Уваров",
    "Федосеев",
    "Харитонов",
    "Цветков",
    "Чернов",
    "Шестаков",
    "Щукин",
    "Юдин",
]
NAMES = [
    "Артём",
    "Борис",
    "Вадим",
    "Глеб",
    "Денис",
    "Егор",
    "Жан",
    "Игорь",
    "Кирилл",
    "Лев",
    "Марк",
    "Никита",
    "Олег",
    "Павел",
    "Роман",
    "Семён",
    "Тимофей",
    "Фёдор",
    "Эдуард",
    "Юрий",
    "Ярослав",
    "Антон",
    "Виктор",
    "Георгий",
    "Матвей",
    "Степан",
]
PATRONYMICS = [
    "Артёмович",
    "Борисович",
    "Вадимович",
    "Глебович",
    "Денисович",
    "Егорович",
    "Игоревич",
    "Кириллович",
    "Львович",
    "Максимович",
    "Никитич",
    "Олегович",
    "Павлович",
    "Романович",
    "Семёнович",
    "Тимофеевич",
    "Фёдорович",
    "Эдуардович",
    "Юрьевич",
    "Ярославович",
    "Андреевич",
    "Викторович",
    "Георгиевич",
    "Матвеевич",
    "Степанович",
    "Антонович",
]
CITIES = [
    "Сортавала",
    "Елец",
    "Кинешма",
    "Тобольск",
    "Арзамас",
    "Выборг",
    "Касимов",
    "Ржев",
    "Таруса",
    "Углич",
    "Зарайск",
    "Торжок",
    "Кунгур",
    "Муром",
    "Кострома",
    "Псков",
    "Вологда",
    "Сызрань",
    "Белозерск",
    "Гатчина",
    "Коломна",
    "Суздаль",
    "Онега",
    "Кыштым",
    "Бийск",
    "Чита",
]
STREETS = [
    "Янтарная",
    "Луговая",
    "Кедровая",
    "Озёрная",
    "Рябиновая",
    "Полярная",
    "Медовая",
    "Лесная",
    "Речная",
    "Солнечная",
    "Тихая",
    "Садовая",
    "Гранитная",
    "Вишнёвая",
    "Берёзовая",
    "Звёздная",
    "Весенняя",
    "Нагорная",
    "Песочная",
    "Кленовая",
    "Малахитовая",
    "Тенистая",
    "Морская",
    "Степная",
    "Таёжная",
    "Сиреневая",
]
ISSUERS = [
    "Отделом МВД России по району Северный",
    "УМВД России по Калужской области",
    "Отделом по вопросам миграции ОМВД России по району Южный",
    "ТП № 4 ОВМ УМВД России по городу Казани",
    "ГУ МВД России по Новосибирской области",
    "Отделом УФМС России по Тверской области",
    "ОВМ МУ МВД России Красноярское",
    "Управлением МВД России по городу Самаре",
    "Отделом МВД России по району Заречный",
    "ТП УФМС России по Пермскому краю",
    "ОВМ ОМВД России по городу Пскову",
    "ГУ МВД России по Ростовской области",
    "Отделом по вопросам миграции по району Центральный",
]


def inn_checksum(prefix: str, weights: list[int]) -> str:
    return str(sum(int(d) * w for d, w in zip(prefix, weights, strict=True)) % 11 % 10)


def make_inn(index: int, length: int) -> str:
    if length == 10:
        prefix = f"{410000000 + index * 7919:09d}"[-9:]
        return prefix + inn_checksum(prefix, [2, 4, 10, 3, 5, 9, 4, 6, 8])
    prefix10 = f"{5100000000 + index * 104729:010d}"[-10:]
    d11 = inn_checksum(prefix10, [7, 2, 4, 10, 3, 5, 9, 4, 6, 8])
    prefix11 = prefix10 + d11
    d12 = inn_checksum(prefix11, [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8])
    return prefix11 + d12


def make_card(index: int, length: int) -> str:
    prefix = "2" + f"{918273645000000000 + index * 3571:018d}"[-(length - 2) :]
    for check in range(10):
        candidate = prefix + str(check)
        total = 0
        parity = len(candidate) % 2
        for pos, char in enumerate(candidate):
            digit = int(char)
            if pos % 2 == parity:
                digit *= 2
                if digit > 9:
                    digit -= 9
            total += digit
        if total % 10 == 0:
            return candidate
    raise AssertionError("unreachable")


def format_digits(value: str, groups: tuple[int, ...], separator: str) -> str:
    out: list[str] = []
    cursor = 0
    for width in groups:
        out.append(value[cursor : cursor + width])
        cursor += width
    return separator.join(out)


def formatted_date(value: date, variant: int) -> str:
    forms = (
        value.strftime("%d.%m.%Y"),
        value.strftime("%d/%m/%Y"),
        value.strftime("%Y-%m-%d"),
        value.strftime("%d-%m-%Y"),
    )
    return forms[variant % len(forms)]


def add_case(cases: list[dict[str, object]], case_id: str, parts: list[object]) -> None:
    text_parts: list[str] = []
    raw_entities: list[tuple[str, str]] = []
    for part in parts:
        if isinstance(part, tuple):
            entity_type, value = part
            text_parts.append(value)
            raw_entities.append((entity_type, value))
        else:
            text_parts.append(str(part))
    text = "".join(text_parts)
    entities: list[dict[str, object]] = []
    cursor = 0
    for entity_type, value in raw_entities:
        start = text.find(value, cursor)
        if start < 0:
            raise AssertionError((case_id, entity_type, value))
        end = start + len(value)
        entities.append({"type": entity_type, "value": value, "start": start, "end": end})
        cursor = end
    cases.append({"id": case_id, "text": text, "entities": entities})


def build_dataset() -> dict[str, object]:
    cases: list[dict[str, object]] = []
    countries = ["Россия", "Казахстан", "Беларусь", "Армения"]
    citizenships = [
        "Российская Федерация",
        "Республика Беларусь",
        "Республика Казахстан",
        "Республика Армения",
    ]

    for group in range(10):
        for j in range(26):
            i = group * 26 + j
            person = f"{SURNAMES[j]} {NAMES[(j + group) % 26]} {PATRONYMICS[(j + 2 * group) % 26]}"
            birth = formatted_date(date(1961, 1, 1) + timedelta(days=i * 173 + 19), i)
            issue = formatted_date(date(2001, 1, 1) + timedelta(days=i * 23 + 11), i + 1)
            city = CITIES[(j + group * 3) % 26]
            street = STREETS[(j * 5 + group) % 26]
            passport_digits = f"{1200 + (i % 7600):04d}{310000 + i * 137:06d}"
            passport = format_digits(passport_digits, (2, 2, 6), (" ", "\u00a0", "-")[i % 3])
            division = f"{100 + (i * 7) % 900:03d}-{100 + (i * 11) % 900:03d}"
            license_digits = f"{10 + i % 89:02d}{10 + (i * 3) % 89:02d}{120000 + i * 211:06d}"
            license_value = format_digits(license_digits, (2, 2, 6), (" ", "\u00a0")[i % 2])
            phone_digits = ("7" if i % 2 == 0 else "8") + f"{9000000000 + i * 3011:010d}"[-10:]
            phone = (
                f"+7 ({phone_digits[1:4]}) {phone_digits[4:7]}-"
                f"{phone_digits[7:9]}-{phone_digits[9:]}"
                if phone_digits[0] == "7"
                else f"8 {phone_digits[1:4]} {phone_digits[4:7]} "
                f"{phone_digits[7:9]} {phone_digits[9:]}"
            )
            email = f"case{i:03d}.qa+v19@sample-{(i % 17) + 1}.example"
            inn = make_inn(i + 37, 10 if i % 2 == 0 else 12)
            card_digits = make_card(i + 71, 16 + i % 4)
            if len(card_digits) == 16:
                card = format_digits(card_digits, (4, 4, 4, 4), (" ", "-")[i % 2])
            else:
                card = card_digits
            cvv = f"{100 + (i * 17) % 900:03d}"
            pin = f"{1000 + (i * 29) % 9000:04d}"
            country = countries[i % len(countries)]
            postal = f"{110000 + i * 113:06d}"[-6:]
            house = f"{1 + i % 199}{'А' if i % 5 == 0 else ''}"
            apartment = str(1 + (i * 13) % 420)
            issuer = ISSUERS[i % len(ISSUERS)]
            cardholder = f"{NAMES[(j + 7) % 26].upper()} {SURNAMES[(j + 11) % 26].upper()}"

            if group == 0:
                parts = [
                    "Анкета: ФИО — ",
                    ("PERSON", person),
                    "; родился ",
                    ("BIRTH_DATE", birth),
                    " в ",
                    ("PLACE_OF_BIRTH", city),
                    "; гражданство: ",
                    ("CITIZENSHIP", citizenships[i % 4]),
                    ".",
                ]
            elif group == 1:
                parts = [
                    "Документ ",
                    ("PASSPORT_RF", passport),
                    ", выдан ",
                    ("PASSPORT_ISSUER", issuer),
                    " ",
                    ("PASSPORT_ISSUE_DATE", issue),
                    ", код ",
                    ("DIVISION_CODE", division),
                    ".",
                ]
            elif group == 2:
                parts = [
                    "Водитель ",
                    ("PERSON", person),
                    " предъявил удостоверение ",
                    ("DRIVER_LICENSE_RF", license_value),
                    "; контакт ",
                    ("PHONE_RF", phone),
                    ".",
                ]
            elif group == 3:
                parts = [
                    "Доставка: страна ",
                    ("ADDRESS_COUNTRY", country),
                    ", индекс ",
                    ("ADDRESS_POSTAL_CODE", postal),
                    ", город ",
                    ("ADDRESS_CITY", city),
                    ", улица ",
                    ("ADDRESS_STREET", street),
                    ", дом ",
                    ("ADDRESS_HOUSE", house),
                    ", квартира ",
                    ("ADDRESS_APARTMENT", apartment),
                    ".",
                ]
            elif group == 4:
                parts = [
                    "Связь с ",
                    ("PERSON", person),
                    ": почта ",
                    ("EMAIL", email),
                    ", телефон ",
                    ("PHONE_RF", phone),
                    "; ИНН ",
                    ("INN", inn),
                    ".",
                ]
            elif group == 5:
                parts = [
                    "Оплата: карта ",
                    ("BANK_CARD", card),
                    "; держатель ",
                    ("CARDHOLDER_NAME", cardholder),
                    "; CVV ",
                    ("CVV", cvv),
                    "; PIN ",
                    ("PIN", pin),
                    "; ИНН плательщика ",
                    ("INN", inn),
                    ".",
                ]
            elif group == 6:
                parts = [
                    "Заявитель ",
                    ("PERSON", person),
                    " | паспорт ",
                    ("PASSPORT_RF", passport),
                    " | дата рождения ",
                    ("BIRTH_DATE", birth),
                    " | тел. ",
                    ("PHONE_RF", phone),
                    " | e-mail ",
                    ("EMAIL", email),
                    " | карта ",
                    ("BANK_CARD", card),
                    ".",
                ]
            elif group == 7:
                parts = [
                    "OCR→ ФИО:",
                    ("PERSON", person),
                    "\nПАСП0РТ:",
                    ("PASSPORT_RF", passport),
                    "\nК0Д П0ДРАЗДЕЛЕНИЯ:",
                    ("DIVISION_CODE", division),
                    "\nВЫДАН:",
                    ("PASSPORT_ISSUER", issuer),
                    "\nДАТА:",
                    ("PASSPORT_ISSUE_DATE", issue),
                    "\u2009",
                ]
            elif group == 8:
                parts = [
                    "payment.card=",
                    ("BANK_CARD", card),
                    "\ncard.holder=",
                    ("CARDHOLDER_NAME", cardholder),
                    "\nsecurity.cvv=",
                    ("CVV", cvv),
                    "\nsecurity.pin=",
                    ("PIN", pin),
                    "\nnotify=",
                    ("EMAIL", email),
                ]
            else:
                parts = [
                    "{user:'",
                    ("PERSON", person),
                    "', birthplace:'",
                    ("PLACE_OF_BIRTH", city),
                    "', dl:'",
                    ("DRIVER_LICENSE_RF", license_value),
                    "', address:{zip:'",
                    ("ADDRESS_POSTAL_CODE", postal),
                    "', city:'",
                    ("ADDRESS_CITY", CITIES[(j + 13) % 26]),
                    "', street:'",
                    ("ADDRESS_STREET", street),
                    "', house:'",
                    ("ADDRESS_HOUSE", house),
                    "', apt:'",
                    ("ADDRESS_APARTMENT", apartment),
                    "'}, phone:'",
                    ("PHONE_RF", phone),
                    "'}",
                ]
            add_case(cases, f"v19-{i + 1:03d}", parts)

    clean_texts = [
        "Сервис ответил 200 OK за 84 мс; повторная попытка не требуется.",
        "Версия протокола 3.28 совместима с форматом JSON UTF-8.",
        "Заказ № 4817 передан в пункт выдачи и ожидает комплектации.",
        "Температура воздуха составит плюс семь градусов, ветер слабый.",
        "Публичная библиотека открыта со вторника по воскресенье.",
        "В отчёте использованы только агрегированные показатели подразделений.",
        "Контрольная сумма файла совпала, повреждений архива не найдено.",
        "Маршрут проходит через площадь, набережную и городской парк.",
        "Лимит очереди равен 4096 сообщениям, таймаут — 30 секунд.",
        "Документация опубликована в открытом репозитории проекта.",
        "Код состояния 503 означает временную недоступность узла.",
        "Модель получила обезличенный текст без пользовательских реквизитов.",
        "Семинар начнётся в девять утра в главном конференц-зале.",
        "Параметр retry_count установлен в 5, режим отладки выключен.",
        "На складе осталось 128 упаковок бумаги формата A4.",
        "Идентификатор трассировки: trace-v19-alpha-0042.",
        "Слово «карта» здесь означает схему проезда по территории музея.",
        "В строке example.invalid намеренно отсутствует почтовый пользователь.",
        "Последовательность 1234 используется как номер шага инструкции.",
        "Сегодня команда проверяет журнал событий и метрики приложения.",
    ]
    for offset, text in enumerate(clean_texts, 261):
        cases.append({"id": f"v19-{offset:03d}", "text": text, "entities": []})

    return {
        "name": "sealed-blind-holdout-v19",
        "version": "19.0.0",
        "sources": ["RAW/requirements.md"],
        "cases": cases,
    }


def main() -> None:
    OUT.write_text(
        json.dumps(build_dataset(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(OUT)


if __name__ == "__main__":
    main()
