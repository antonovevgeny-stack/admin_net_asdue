.PHONY: deploy logs stop clean status monitor backup

deploy:
	@echo "Starting deployment..."
	@./deploy.sh

logs:
	@docker compose logs -f

stop:
	@docker compose down

clean:
	@docker compose down -v
	@docker system prune -af

status:
	@docker compose ps

monitor:
	@echo "=== Container Status ==="
	@docker compose ps
	@echo -e "\n=== Resource Usage ==="
	@docker stats --no-stream
	@echo -e "\n=== Recent Logs ==="
	@docker compose logs --tail=20

restart:
	@docker compose restart
	@echo "Services restarted"

update:
	@git pull
	@./deploy.sh

backup:
	@mkdir -p backups
	@tar -czf "backups/backup_$(date +%Y%m%d_%H%M%S).tar.gz" \
		--exclude=logs \
		--exclude=backups \
		--exclude=.git \
		.
	@echo "Backup created in backups/"

help:
	@echo "Available commands:"
	@echo "  make deploy    - Deploy the application"
	@echo "  make logs      - View logs"
	@echo "  make stop      - Stop services"
	@echo "  make status    - Check container status"
	@echo "  make monitor   - Monitor resources"
	@echo "  make restart   - Restart services"
	@echo "  make backup    - Create backup"
	@echo "  make clean     - Stop and clean all containers/images"
