#!/bin/bash
set -e

PROJECT_PATH="/home/asdue/netadminASDUE"
cd "$PROJECT_PATH"

case "$1" in
    start)
        echo "Запуск АСДУЕ..."
        docker compose up -d
        echo "Готово! Откройте http://localhost"
        ;;
    stop)
        echo "Остановка АСДУЕ..."
        docker compose down
        echo "Остановлено"
        ;;
    restart)
        echo "Перезапуск АСДУЕ..."
        docker compose restart
        echo "Перезапущено"
        ;;
    status)
        echo "Статус контейнеров:"
        docker compose ps
        echo ""
        echo "Использование ресурсов:"
        docker stats --no-stream
        ;;
    logs)
        echo "Логи контейнеров:"
        docker compose logs -f
        ;;
    update)
        echo "Обновление проекта..."
        git pull
        ./deploy.sh
        ;;
    backup)
        echo "Создание резервной копии..."
        BACKUP_DIR="backups"
        BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).tar.gz"
        mkdir -p "$BACKUP_DIR"
        tar -czf "$BACKUP_FILE" \
            --exclude=logs \
            --exclude=backups \
            --exclude=.git \
            --exclude=*.pyc \
            .
        echo "Резервная копия создана: $BACKUP_FILE"
        ;;
    help|*)
        echo "Использование: $0 {start|stop|restart|status|logs|update|backup|help}"
        echo ""
        echo "Команды:"
        echo "  start    - Запустить проект"
        echo "  stop     - Остановить проект"
        echo "  restart  - Перезапустить проект"
        echo "  status   - Показать статус контейнеров"
        echo "  logs     - Показать логи (режим слежения)"
        echo "  update   - Обновить проект из git и перезапустить"
        echo "  backup   - Создать резервную копию"
        echo "  help     - Показать эту справку"
        ;;
esac
