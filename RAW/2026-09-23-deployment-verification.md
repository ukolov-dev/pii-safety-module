# Проверка развёртывания модуля ПД

Дата: 23.09.2026. Факт: результаты команд текущей задачи, без секретных значений.
Авторизация: [запрос пользователя](2026-09-23-deployment-request.md).

## Локальная реализация

- Изменены solution/app/consumers.py, main.py, service.py, settings.py,
  observability.py, vault/redis.py, Dockerfile; добавлены deploy-конфиги и интеграционные тесты.
- Сохранены исходные предшествующие изменения; детектор, подключённый через
  app/detection/__init__.py, остался v3.26.
- Полный pytest: 237 passed, 1 предупреждение о deprecated TestClient/httpx.
- Ruff для затронутых Python-модулей и нового теста: успешно.
- mypy для consumers/main/service/settings/observability: успешно.

## VPS и маршруты

- SSH: srvadmin, hostname srv1587127; sudo -n whoami: root.
- Сервис: Compose project pii-safety; API и Redis healthy.
- Релиз: /opt/projects/pii-safety/releases/20260923-consumers.
- Compose: deploy/compose.vps.yml внутри релиза; постоянные ключи —
  /opt/projects/pii-safety/.env (root, 0600), значения не выводились.
- API опубликован только локально: 127.0.0.1:18089; Redis без host-порта.
- nginx demo-hr переключён на PII; HR-файлы не удалены.
- nginx -t: успешно; reload: успешно.
- https://demo.vibecodefromvoronezh.com/health/ready: 200, {"status":"ok"},
  проверено с VPS и локального компьютера.
- /docs: 200; /metrics снаружи: 404.

## Проверки поведения по HTTPS

- Маскирование тестового email/телефона, повтор исходного запроса и точное восстановление: успешно.
- Неизвестный потребитель: 403; partner без ключа: 401; с серверным ключом: 200.
- Другой потребитель с тем же payload_id не получил исходные значения: успешно.
- docker restart только pii-safety-api-1; после readiness восстановление прежнего payload: успешно.
- В последних логах есть identified, но нет тестового исходного email, payload_id или ключа.

## Наблюдаемость

- Prometheus config проверен promtool; reload через HUP без остановки контейнера.
- Цель pii-safety-api:8080: up{job="pii-safety"}=1.
- Grafana provisioning загрузил uid=pii-safety, title="PII Safety — demo";
  datasource uid=prometheus существует.
- Панели: RPS, latency p95, TPS (whitespace), ошибки 4xx/5xx, доступность.
- Ограничение: TPS — счётчик непробельных последовательностей, не токенизация модели.

## Резервные копии и ограничения

- /opt/projects/pii-safety/backups/20260923-before-demo/{demo-hr.conf,prometheus.yml};
  каталог 0700, файлы 0600.
- Публичный portal оставлен намеренно для контракта проверки; partner использует ключ.
- Redis без persistence: перезапуск Redis теряет краткоживущие соответствия.
- Нагрузочная проверка 1000 RPS именно этого развёртывания не выполнялась.
- Требование качества 95% не переоценивалось и не объявляется выполненным.
