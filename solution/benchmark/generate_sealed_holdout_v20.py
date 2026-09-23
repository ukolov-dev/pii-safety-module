"""Generate the independent canonical blind holdout v20.

The file deliberately contains no detector imports.  It is generated and hashed
before any candidate detector is evaluated.
"""

from __future__ import annotations

import hashlib
import json
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 20_260_923
ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "sealed_holdout_v20.json"

PERSONS = [
    "Капустина Инесса Вадимовна",
    "Черепанов Марк Юрьевич",
    "Шаповалова Софья Ильинична",
    "Логинов Денис Анатольевич",
    "Фокина Алина Романовна",
    "Белоусов Никита Олегович",
    "Зорина Марина Евгеньевна",
    "Устинов Глеб Сергеевич",
    "Новикова Вера Павловна",
    "Кулешов Тимофей Андреевич",
    "Рябова Элина Валерьевна",
    "Савин Арсений Михайлович",
]
PLACES = [
    "Абакан",
    "Листвянка",
    "Великие Луки",
    "Дивеево",
    "Норильск",
    "Териберка",
    "Кострома",
    "Константиново",
]
CITIES = [
    "Абакан",
    "Архангельск",
    "Белгород",
    "Вологда",
    "Ижевск",
    "Калуга",
    "Кострома",
    "Курган",
    "Мурманск",
    "Орёл",
    "Псков",
    "Тамбов",
]
STREETS = [
    "Каменная",
    "Энергетиков",
    "Северный",
    "Геологов",
    "Речной",
    "Лесное",
    "Озёрная",
    "Маячный",
]
ISSUERS = [
    "ОВМ УМВД России по г. Калуге",
    "Отделом МВД России по Псковскому району",
    "ГУ МВД России по Мурманской области",
    "ОТДЕЛЕНИЕ УФМС РОССИИ ПО КУРГАНСКОЙ ОБЛ.",
    "ОВМ ОМВД России по Октябрьскому району",
    "УМВД России по городу Белгороду",
]
CITIZENSHIPS = ["Российская Федерация", "Россия", "РФ"]
COUNTRIES = ["Россия", "Российская Федерация"]


def luhn_complete(prefix: str) -> str:
    for digit in "0123456789":
        number = prefix + digit
        total = 0
        parity = len(number) % 2
        for index, char in enumerate(number):
            value = int(char)
            if index % 2 == parity:
                value *= 2
                if value > 9:
                    value -= 9
            total += value
        if total % 10 == 0:
            return number
    raise AssertionError("unreachable")


def inn12(prefix10: str) -> str:
    digits = [int(c) for c in prefix10]
    c11 = sum(a * b for a, b in zip(digits, [7, 2, 4, 10, 3, 5, 9, 4, 6, 8], strict=True)) % 11 % 10
    digits.append(c11)
    c12 = (
        sum(a * b for a, b in zip(digits, [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8], strict=True))
        % 11
        % 10
    )
    return "".join(map(str, digits)) + str(c12)


def formatted_date(index: int, offset: int = 0) -> str:
    value = date(1955, 1, 1) + timedelta(days=(index * 397 + offset * 137) % 18_000)
    return [value.strftime("%d.%m.%Y"), value.strftime("%d-%m-%Y"), value.strftime("%d/%m/%Y")][
        index % 3
    ]


def passport(index: int) -> str:
    raw = f"{1100 + index % 89:04d}{210000 + index * 719:06d}"[-10:]
    return f"{raw[:4]} {raw[4:]}"


def license_number(index: int) -> str:
    raw = f"{2300 + index % 91:04d}{310000 + index * 617:06d}"[-10:]
    return f"{raw[:2]} {raw[2:4]} {raw[4:]}"


def phone(index: int) -> str:
    subscriber = (1_000_000 + index * 7_919) % 10_000_000
    raw = f"7{900 + index % 90:03d}{subscriber:07d}"
    if index % 3 == 0:
        return f"+7 ({raw[1:4]}) {raw[4:7]}-{raw[7:9]}-{raw[9:]}"
    if index % 3 == 1:
        return f"8 {raw[1:4]} {raw[4:7]} {raw[7:9]} {raw[9:]}"
    return raw


def card(index: int) -> str:
    raw = luhn_complete(f"427640{100000000 + index * 3571:09d}"[-15:])
    if index % 3 == 0:
        return " ".join(raw[pos : pos + 4] for pos in range(0, 16, 4))
    if index % 3 == 1:
        return "-".join(raw[pos : pos + 4] for pos in range(0, 16, 4))
    return raw


def render(template: str, values: dict[str, str]) -> tuple[str, list[dict[str, object]]]:
    text = template
    entities: list[dict[str, object]] = []
    for entity_type, value in values.items():
        marker = "{" + entity_type + "}"
        if marker not in text:
            raise AssertionError(f"missing marker {marker}")
        start = text.index(marker)
        text = text.replace(marker, value, 1)
        entities.append(
            {"type": entity_type, "value": value, "start": start, "end": start + len(value)}
        )
    entities.sort(key=lambda item: int(item["start"]))
    return text, entities


def values(index: int) -> dict[str, str]:
    first, last = PERSONS[index % len(PERSONS)].split()[1], PERSONS[index % len(PERSONS)].split()[0]
    return {
        "PERSON": PERSONS[index % len(PERSONS)],
        "BIRTH_DATE": formatted_date(index),
        "PLACE_OF_BIRTH": PLACES[index % len(PLACES)],
        "CITIZENSHIP": CITIZENSHIPS[index % len(CITIZENSHIPS)],
        "PASSPORT_RF": passport(index),
        "PASSPORT_ISSUER": ISSUERS[index % len(ISSUERS)],
        "DIVISION_CODE": f"{101 + index % 798:03d}-{110 + (index * 17) % 889:03d}",
        "PASSPORT_ISSUE_DATE": formatted_date(index, 41),
        "DRIVER_LICENSE_RF": license_number(index),
        "ADDRESS_COUNTRY": COUNTRIES[index % len(COUNTRIES)],
        "ADDRESS_POSTAL_CODE": f"{101000 + (index * 2089) % 899000:06d}",
        "ADDRESS_CITY": CITIES[index % len(CITIES)],
        "ADDRESS_STREET": STREETS[index % len(STREETS)],
        "ADDRESS_HOUSE": f"{1 + index % 187}{['', 'А', 'Б'][index % 3]}",
        "ADDRESS_APARTMENT": str(1 + (index * 13) % 340),
        "EMAIL": f"{first.lower()}.{last.lower()}{index}@mailbox-test.ru",
        "PHONE_RF": phone(index),
        "INN": inn12(f"{5000000000 + index * 7919:010d}"[-10:]),
        "BANK_CARD": card(index),
        "CVV": f"{100 + (index * 37) % 900:03d}",
        "PIN": f"{1000 + (index * 73) % 9000:04d}",
        "CARDHOLDER_NAME": f"{first.upper()} {last.upper()}",
    }


TEMPLATES = [
    (
        "identity-prose",
        "Клиент {PERSON}, дата рождения {BIRTH_DATE}; "
        "место рождения: {PLACE_OF_BIRTH}; гражданство — {CITIZENSHIP}.",
        ("PERSON", "BIRTH_DATE", "PLACE_OF_BIRTH", "CITIZENSHIP"),
    ),
    (
        "passport-ocr",
        "ПАСПОРТ РФ\nСЕРИЯ/НОМЕР {PASSPORT_RF}\n"
        "ВЫДАН {PASSPORT_ISSUER}\nКОД {DIVISION_CODE}\n"
        "ДАТА ВЫДАЧИ {PASSPORT_ISSUE_DATE}",
        ("PASSPORT_RF", "PASSPORT_ISSUER", "DIVISION_CODE", "PASSPORT_ISSUE_DATE"),
    ),
    (
        "contact-config",
        "owner={PERSON}\nlicense_rf={DRIVER_LICENSE_RF}\ncontact_email={EMAIL}\nmobile={PHONE_RF}",
        ("PERSON", "DRIVER_LICENSE_RF", "EMAIL", "PHONE_RF"),
    ),
    (
        "address-json",
        '{{"country":"{ADDRESS_COUNTRY}","postal_code":"{ADDRESS_POSTAL_CODE}","city":"{ADDRESS_CITY}","street":"{ADDRESS_STREET}","house":"{ADDRESS_HOUSE}","apartment":"{ADDRESS_APARTMENT}"}}',
        (
            "ADDRESS_COUNTRY",
            "ADDRESS_POSTAL_CODE",
            "ADDRESS_CITY",
            "ADDRESS_STREET",
            "ADDRESS_HOUSE",
            "ADDRESS_APARTMENT",
        ),
    ),
    (
        "bank-prose",
        "Для карты {BANK_CARD} на имя {CARDHOLDER_NAME} указаны CVV {CVV} и ПИН {PIN}.",
        ("BANK_CARD", "CARDHOLDER_NAME", "CVV", "PIN"),
    ),
    (
        "mixed-ticket",
        "Заявка: {PERSON}; ИНН {INN}; телефон {PHONE_RF}; e-mail {EMAIL}; город {ADDRESS_CITY}.",
        ("PERSON", "INN", "PHONE_RF", "EMAIL", "ADDRESS_CITY"),
    ),
    (
        "mixed-json",
        '{{"customer":"{PERSON}","birth":"{BIRTH_DATE}","passport":"{PASSPORT_RF}","inn":"{INN}","phone":"{PHONE_RF}"}}',
        ("PERSON", "BIRTH_DATE", "PASSPORT_RF", "INN", "PHONE_RF"),
    ),
]

CLEAN_TEXTS = [
    "Сервис готов к обработке запросов, очередь пуста.",
    "В отчёте описаны общие принципы защиты данных без сведений о клиентах.",
    "mode=masked\nretry=enabled\nregion=central",
    '{"status":"ok","message":"personal data is absent"}',
    "Оператор подтвердил, что форма не содержит реквизитов.",
    "Адрес и номер документа не были указаны.",
    "Карта клиента ещё не выпущена, платёжных реквизитов нет.",
    "Для отладки используйте только обезличенные примеры.",
]


def alphabetic_code(index: int) -> str:
    """Return a stable digit-free two-letter scenario code."""
    alphabet = "абвгдежзиклмнопрстуфхцчшщэюя"
    return alphabet[index // len(alphabet)] + alphabet[index % len(alphabet)]


def main() -> None:
    rng = random.Random(SEED)
    cases: list[dict[str, object]] = []
    # 280 positive/mixed records. Each base family occurs 40 times, so every
    # required type has at least 40 independently generated annotations.
    schedule = [index % len(TEMPLATES) for index in range(280)]
    rng.shuffle(schedule)
    for number, template_index in enumerate(schedule, start=1):
        family, template, keys = TEMPLATES[template_index]
        generated = values(number * 19 + template_index * 101)
        text, entities = render(template, {key: generated[key] for key in keys})
        cases.append(
            {"id": f"v20-{number:03d}", "family": family, "text": text, "entities": entities}
        )

    # Forty clean negatives across prose, configuration and JSON contexts.
    for clean_index in range(40):
        text = (
            CLEAN_TEXTS[clean_index % len(CLEAN_TEXTS)]
            + f" Сценарий {alphabetic_code(clean_index)}."
        )
        cases.append(
            {
                "id": f"v20-{len(cases) + 1:03d}",
                "family": "clean-negative",
                "text": text,
                "entities": [],
            }
        )

    payload = {
        "name": "sealed-holdout-v20",
        "version": 20,
        "seed": SEED,
        "sources": ["RAW/requirements.md"],
        "annotation_convention": "Exact value spans; labels/designators are excluded.",
        "cases": cases,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    digest = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    print(f"wrote {len(cases)} cases to {OUTPUT}")
    print(f"sha256={digest}")


if __name__ == "__main__":
    main()
