# 🚀 Руководство по развертыванию

Полное руководство по развертыванию Telegram Calendar Bot в различных окружениях.

## 📋 Содержание

1. [Требования к системе](#требования-к-системе)
2. [Локальная разработка](#локальная-разработка)
3. [Docker развертывание](#docker-развертывание)
4. [Продакшн установка](#продакшн-установка)
5. [Kubernetes](#kubernetes)
6. [Мониторинг и логирование](#мониторинг-и-логирование)
7. [Резервное копирование](#резервное-копирование)

## 🖥 Требования к системе

### Минимальные требования
- **CPU**: 1 ядро, 2GHz
- **RAM**: 512MB
- **Диск**: 2GB свободного места
- **ОС**: Linux/macOS/Windows с Docker

### Рекомендуемые требования (продакшн)
- **CPU**: 2+ ядра
- **RAM**: 1GB+
- **Диск**: 10GB+ (логи, резервные копии)
- **ОС**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+

### Зависимости
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y docker.io docker-compose git python3 python3-pip

# CentOS/RHEL
sudo yum install -y docker docker-compose git python3 python3-pip
sudo systemctl start docker
sudo systemctl enable docker

# macOS (с Homebrew)
brew install docker docker-compose git python@3.11
```

## 🛠 Локальная разработка

### Шаг 1: Клонирование
```bash
git clone https://github.com/your-username/telegram-calendar-bot.git
cd telegram-calendar-bot
```

### Шаг 2: Виртуальное окружение
```bash
# Создание виртуального окружения
python3 -m venv venv

# Активация (Linux/macOS)
source venv/bin/activate

# Активация (Windows)
venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt
```

### Шаг 3: Конфигурация
```bash
# Создание .env файла
cp .env.example .env

# Редактирование конфигурации
nano .env  # или vim .env
```

Пример `.env` файла:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
GOOGLE_CALENDAR_ID=your@gmail.com
GOOGLE_CREDENTIALS_FILE=./credentials.json
RATE_LIMIT_PER_MINUTE=20
LOG_LEVEL=DEBUG
```

### Шаг 4: Тестовый запуск
```bash
# Запуск тестов
pytest

# Запуск бота
python -m src.cli start
```

## 🐳 Docker развертывание

### Быстрый запуск (разработка)
```bash
# Сборка и запуск
make dev

# Или вручную
docker-compose up --build
```

### Кастомизация docker-compose.yml

#### Базовая настройка
```yaml
version: '3.8'
services:
  telegram-calendar-bot:
    build: .
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
```

#### С мониторингом
```yaml
version: '3.8'
services:
  telegram-calendar-bot:
    # ... базовая настройка ...
    logging:
      driver: "fluentd"
      options:
        fluentd-address: "localhost:24224"
        tag: "telegram-bot"
        
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### Переменные окружения для Docker

| Переменная | Значение по умолчанию | Описание |
|------------|---------------------|----------|
| `TELEGRAM_BOT_TOKEN` | - | **Обязательно**: Токен бота |
| `GOOGLE_CALENDAR_ID` | - | ID календаря Google |
| `RATE_LIMIT_PER_MINUTE` | `20` | Лимит запросов |
| `LOG_LEVEL` | `INFO` | Уровень логирования |
| `PYTHONUNBUFFERED` | `1` | Отключение буферизации |

## 🔧 Продакшн установка

### Подготовка сервера
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Создание пользователя для бота
sudo useradd -m -s /bin/bash telegram-bot
sudo usermod -aG docker telegram-bot

# Создание директорий
sudo mkdir -p /opt/telegram-calendar-bot
sudo chown telegram-bot:telegram-bot /opt/telegram-calendar-bot
```

### Развертывание
```bash
# Переключение на пользователя бота
sudo su - telegram-bot

# Клонирование в продакшн директорию
cd /opt/telegram-calendar-bot
git clone https://github.com/your-username/telegram-calendar-bot.git .

# Настройка продакшн конфигурации
cp .env.example .env.prod
nano .env.prod
```

Продакшн `.env.prod`:
```env
TELEGRAM_BOT_TOKEN=your_production_token
GOOGLE_CALENDAR_ID=your@gmail.com
GOOGLE_CREDENTIALS_FILE=/app/credentials.json
RATE_LIMIT_PER_MINUTE=50
LOG_LEVEL=INFO
PYTHONUNBUFFERED=1
```

### Продакшн развертывание
```bash
# Автоматическое развертывание
./scripts/deploy.sh prod

# Или поэтапно
make build
make backup  # если обновляете существующую установку
docker-compose -f docker-compose.prod.yml up -d
```

### Systemd сервис (альтернатива Docker)
Создайте systemd сервис:

```bash
sudo nano /etc/systemd/system/telegram-calendar-bot.service
```

Содержимое:
```ini
[Unit]
Description=Telegram Calendar Bot
After=network.target

[Service]
Type=simple
User=telegram-bot
WorkingDirectory=/opt/telegram-calendar-bot
Environment=PATH=/opt/telegram-calendar-bot/venv/bin
ExecStart=/opt/telegram-calendar-bot/venv/bin/python -m src.cli start
ExecStop=/opt/telegram-calendar-bot/venv/bin/python -m src.cli stop
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Запуск сервиса:
```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-calendar-bot
sudo systemctl start telegram-calendar-bot
sudo systemctl status telegram-calendar-bot
```

## ☸️ Kubernetes

### Namespace
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: telegram-bot
```

### ConfigMap
```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: telegram-bot-config
  namespace: telegram-bot
data:
  LOG_LEVEL: "INFO"
  RATE_LIMIT_PER_MINUTE: "50"
  GOOGLE_CALENDAR_ID: "your@gmail.com"
```

### Secret
```yaml
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: telegram-bot-secrets
  namespace: telegram-bot
type: Opaque
data:
  telegram-bot-token: <base64-encoded-token>
  google-credentials: <base64-encoded-json>
```

### Deployment
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: telegram-calendar-bot
  namespace: telegram-bot
spec:
  replicas: 1
  selector:
    matchLabels:
      app: telegram-calendar-bot
  template:
    metadata:
      labels:
        app: telegram-calendar-bot
    spec:
      containers:
      - name: telegram-bot
        image: telegram-calendar-bot:latest
        env:
        - name: TELEGRAM_BOT_TOKEN
          valueFrom:
            secretKeyRef:
              name: telegram-bot-secrets
              key: telegram-bot-token
        envFrom:
        - configMapRef:
            name: telegram-bot-config
        resources:
          limits:
            memory: "512Mi"
            cpu: "500m"
          requests:
            memory: "256Mi"
            cpu: "100m"
        livenessProbe:
          exec:
            command:
            - /app/healthcheck.sh
          initialDelaySeconds: 30
          periodSeconds: 30
        volumeMounts:
        - name: google-credentials
          mountPath: /app/credentials.json
          subPath: credentials.json
          readOnly: true
      volumes:
      - name: google-credentials
        secret:
          secretName: telegram-bot-secrets
          items:
          - key: google-credentials
            path: credentials.json
```

### Развертывание в Kubernetes
```bash
# Применение всех манифестов
kubectl apply -f k8s/

# Проверка статуса
kubectl get pods -n telegram-bot
kubectl logs -f deployment/telegram-calendar-bot -n telegram-bot

# Масштабирование (не рекомендуется для Telegram ботов)
kubectl scale deployment telegram-calendar-bot --replicas=1 -n telegram-bot
```

## 📊 Мониторинг и логирование

### Prometheus метрики
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'telegram-bot'
    static_configs:
      - targets: ['telegram-calendar-bot:8080']

rule_files:
  - "alert_rules.yml"
```

### Grafana дашборд
```json
{
  "dashboard": {
    "title": "Telegram Calendar Bot",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(telegram_requests_total[5m])"
          }
        ]
      }
    ]
  }
}
```

### ELK Stack логирование
```yaml
# docker-compose.monitoring.yml
version: '3.8'
services:
  elasticsearch:
    image: elasticsearch:7.14.0
    environment:
      - discovery.type=single-node
    volumes:
      - es-data:/usr/share/elasticsearch/data

  logstash:
    image: logstash:7.14.0
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline

  kibana:
    image: kibana:7.14.0
    ports:
      - "5601:5601"
    environment:
      ELASTICSEARCH_HOSTS: http://elasticsearch:9200

volumes:
  es-data:
```

## 💾 Резервное копирование

### Автоматическое резервное копирование
```bash
# Cron job для ежедневного резервного копирования
0 2 * * * /opt/telegram-calendar-bot/scripts/backup.sh create

# Еженедельная очистка старых копий
0 3 * * 0 /opt/telegram-calendar-bot/scripts/backup.sh cleanup --retention-days 7
```

### Резервное копирование в облако
```bash
# AWS S3
aws s3 sync ./backups/ s3://your-bucket/telegram-bot-backups/

# Google Cloud Storage
gsutil -m rsync -r ./backups/ gs://your-bucket/telegram-bot-backups/

# Включение в скрипт резервного копирования
echo "aws s3 cp \$backup_file s3://your-bucket/telegram-bot-backups/" >> scripts/backup.sh
```

## 🔧 Обновление

### Обновление Docker развертывания
```bash
# Получение последней версии
git pull origin main

# Обновление через Make
make update

# Или через скрипт развертывания
./scripts/deploy.sh update
```

### Откат к предыдущей версии
```bash
# Автоматический откат
./scripts/deploy.sh rollback

# Ручной откат
git revert HEAD
make build
docker-compose up -d
```

### Zero-downtime обновления
```bash
# Использование Blue-Green развертывания
docker-compose -f docker-compose.blue.yml up -d
# Тестирование новой версии
docker-compose -f docker-compose.yml down
docker-compose -f docker-compose.blue.yml down
```

## 🆘 Устранение неполадок

### Проверка статуса
```bash
# Docker контейнеры
docker ps
docker logs telegram-calendar-bot

# Системные ресурсы
docker stats

# Проверка здоровья
./scripts/healthcheck.sh
```

### Частые проблемы

#### Контейнер не запускается
```bash
# Проверка логов
docker-compose logs telegram-calendar-bot

# Проверка конфигурации
docker-compose config

# Пересборка образа
docker-compose build --no-cache
```

#### Нет доступа к Google Calendar
```bash
# Проверка credentials
ls -la credentials.json

# Проверка переменных окружения
docker exec telegram-calendar-bot env | grep GOOGLE

# Проверка логов аутентификации
docker logs telegram-calendar-bot | grep "google\|calendar\|auth"
```

#### Высокое использование памяти
```bash
# Ограничение памяти в docker-compose.yml
deploy:
  resources:
    limits:
      memory: 512M

# Мониторинг использования памяти
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

## 📞 Поддержка

При возникновении проблем:

1. **Проверьте логи**: `docker-compose logs -f`
2. **Запустите health check**: `./scripts/healthcheck.sh`
3. **Проверьте документацию**: [docs/faq.md](faq.md)
4. **Создайте issue**: [GitHub Issues](https://github.com/your-username/telegram-calendar-bot/issues)

---

*Документация актуальна для версии 1.0.0*