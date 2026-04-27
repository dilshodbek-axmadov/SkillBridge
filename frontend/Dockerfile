# =============================================================================
# SkillBridge frontend — Vite + React, served by Nginx.
#
# Vite env vars (VITE_*) are baked into the JS bundle at BUILD TIME, so they
# must be passed in via --build-arg from the CI workflow:
#
#   docker build \
#     --build-arg VITE_API_BASE_URL=https://skillbridge-api.azurewebsites.net/api/v1 \
#     --build-arg VITE_GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com \
#     -t skillbridge-frontend:latest .
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: build the React app with Vite
# -----------------------------------------------------------------------------
FROM node:20-alpine AS build-stage

WORKDIR /app

# Install deps from lockfile (deterministic, faster than `npm install`)
COPY package.json package-lock.json ./
RUN npm ci

# Build args -> ENV so Vite can read them as import.meta.env.VITE_*
ARG VITE_API_BASE_URL
ARG VITE_GOOGLE_CLIENT_ID
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_GOOGLE_CLIENT_ID=${VITE_GOOGLE_CLIENT_ID}

# Copy source and build
COPY . .
RUN npm run build


# -----------------------------------------------------------------------------
# Stage 2: serve the static bundle via Nginx
# -----------------------------------------------------------------------------
FROM nginx:stable-alpine AS runtime

# Replace the default site config with our SPA-aware one
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the Vite build output
COPY --from=build-stage /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
