#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Starting production deployment for АСДУЕ...${NC}"

echo -e "${YELLOW}Checking required files...${NC}"
[ -f "docker-compose.yml" ] || { echo -e "${RED}docker-compose.yml not found${NC}"; exit 1; }
[ -f "Dockerfile" ] || { echo -e "${RED}Dockerfile not found${NC}"; exit 1; }
[ -f "requirements.txt" ] || { echo -e "${RED}requirements.txt not found${NC}"; exit 1; }
[ -f "nginx.conf" ] || { echo -e "${RED}nginx.conf not found${NC}"; exit 1; }

echo -e "${YELLOW}Checking port 80 availability...${NC}"
if command -v netstat &> /dev/null; then
    if netstat -tuln | grep ':80 ' | grep LISTEN; then
        echo -e "${RED}Port 80 is already in use!${NC}"
        echo -e "${YELLOW}Please stop services using port 80:${NC}"
        echo -e "  sudo systemctl stop nginx"
        echo -e "  sudo systemctl stop apache2"
        exit 1
    fi
fi

echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p logs/nginx logs/app static ssl

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}.env file not found, creating from example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Generated .env file. Please edit it with your settings.${NC}"
    echo -e "${YELLOW}IMPORTANT: Change APP_SECRET_KEY in .env file!${NC}"
    read -p "Press Enter to continue or Ctrl+C to exit and edit .env..."
fi

if grep -q "your-secure-secret-key-change-me" .env; then
    echo -e "${YELLOW}Generating new secret key...${NC}"
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32)
    sed -i "s|APP_SECRET_KEY=.*|APP_SECRET_KEY=$SECRET_KEY|" .env
    echo -e "${GREEN}✓ Secret key generated${NC}"
fi

echo -e "${YELLOW}Stopping old containers...${NC}"
docker compose down --remove-orphans || true

echo -e "${YELLOW}Cleaning old images...${NC}"
docker system prune -f

echo -e "${YELLOW}Building new images...${NC}"
docker compose build --no-cache

echo -e "${YELLOW}Starting services...${NC}"
docker compose up -d

echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 15

echo -e "${YELLOW}Checking health status...${NC}"
if curl -f http://localhost/health >/dev/null 2>&1; then
    echo -e "${GREEN}✓ All services are up and running!${NC}"
else
    echo -e "${RED}✗ Some services failed to start${NC}"
    echo -e "${YELLOW}Showing logs:${NC}"
    docker compose logs --tail=50
    exit 1
fi

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo ""
echo -e "${YELLOW}=== АСДУЕ Deployment Summary ===${NC}"
echo -e "Dashboard URL: ${GREEN}http://localhost${NC}"
echo -e "API Health:    http://localhost/health"
echo -e "IP Calculator: http://localhost/api/ip-calculator"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo -e "  docker compose logs -f     # View logs"
echo -e "  docker compose ps          # Check status"
echo -e "  docker compose restart     # Restart services"
echo -e "  ./deploy.sh                # Redeploy"
echo ""
echo -e "${GREEN}✓ Аудит сети АСДУЕ is now running on port 80!${NC}"
