FROM node:24-slim

# Set memory limits for Node.js
ENV NODE_OPTIONS="--max-old-space-size=1024"

WORKDIR /app

# Copy package.json first
COPY package.json ./

# Clean npm cache and install dependencies with production optimizations
RUN npm cache clean --force && \
    npm install --silent
# Copy source code
COPY . .


# Create .next directory and set permissions before switching user
RUN mkdir -p /app/.next /app/node_modules 

# Expose port
EXPOSE 3010

# Start development server with memory optimization
CMD ["node", "--max-old-space-size=1024", "node_modules/.bin/next", "dev", "--turbopack", "--port", "3010"]