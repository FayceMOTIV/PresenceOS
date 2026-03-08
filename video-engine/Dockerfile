FROM node:20-bookworm-slim

# Libs système requises pour Chromium headless sur Linux
RUN apt-get update && apt-get install -y \
  libnss3 \
  libdbus-1-3 \
  libatk1.0-0 \
  libgbm-dev \
  libasound2 \
  libxrandr2 \
  libxkbcommon-dev \
  libxfixes3 \
  libxcomposite1 \
  libxdamage1 \
  libatk-bridge2.0-0 \
  libcups2 \
  libdrm2 \
  libx11-xcb1 \
  libxcb-dri3-0 \
  wget \
  ca-certificates \
  fonts-liberation \
  --no-install-recommends \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Build TypeScript server
RUN npm run build

# Pre-download Remotion browser at build time (avoids cold start download)
RUN npx remotion browser ensure

# Railway memory hint
ENV NODE_OPTIONS="--max-old-space-size=1024"
ENV PORT=3001

EXPOSE 3001

CMD ["node", "dist/server.js"]
