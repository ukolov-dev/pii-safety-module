# Развёртывание и откат demo

Фактический релиз: `/opt/projects/pii-safety/releases/20260923-consumers`.
Compose project: `pii-safety`, конфиг `deploy/compose.vps.yml`.
Ключи находятся только в серверном `/opt/projects/pii-safety/.env`, root 0600;
передавать их в Compose через `--env-file`, не выводить `compose config` без `--quiet`.

## Проверка

```sh
sudo -n docker compose -p pii-safety --env-file /opt/projects/pii-safety/.env -f /opt/projects/pii-safety/releases/20260923-consumers/deploy/compose.vps.yml ps
curl -fsS https://demo.vibecodefromvoronezh.com/health/ready
sudo -n docker logs --since 5m --tail 100 pii-safety-api-1
```

Панель: https://monitoring.vibecodefromvoronezh.com/d/pii-safety.
Метрики доступны через localhost:18089/metrics или внутри monitoring_monitoring.
Не публиковать Redis и /metrics наружу.

## Откат маршрута

Backup: `/opt/projects/pii-safety/backups/20260923-before-demo` (root 0700).
Для возврата HR восстановить demo-hr.conf в `/etc/nginx/sites-available/demo-hr`,
проверить `nginx -t`, затем `systemctl reload nginx`; HR-файлы не удалены.
Для удаления scrape-цели восстановить prometheus.yml из backup в существующий
файл `/opt/projects/monitoring/prometheus/prometheus.yml`, сохранив inode bind mount
(через перенаправление содержимого), проверить promtool и отправить HUP контейнеру
monitoring-prometheus-1. Не заменять конфиг старым backup, если после деплоя в него
внесены другие изменения: в таком случае удалить только добавленную scrape-цель.
Не применять compose down к другим проектам и не удалять volumes.

## Обновление

Собрать новый отдельный каталог releases, сохранить текущие настройки и ключи,
проверить тесты и Compose config --quiet, затем выполнить up -d --build только
проекта pii-safety с новым путём конфига. После обновления проверить readiness,
маскирование/восстановление, authentication, метрики и логи.
