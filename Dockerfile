# Stage 1: Build the React frontend
FROM oven/bun:1 AS frontend-builder

WORKDIR /app

# Copy package.json and bun.lockb
COPY package.json bun.lockb ./

# Install frontend dependencies
RUN bun install --frozen-lockfile

# Copy the rest of the frontend application code
COPY ./public ./public
COPY ./src ./src
COPY ./vite.config.ts ./vite.config.ts
COPY ./tsconfig.json ./tsconfig.json
COPY ./tsconfig.app.json ./tsconfig.app.json
COPY ./tsconfig.node.json ./tsconfig.node.json
COPY ./index.html ./index.html
COPY ./tailwind.config.ts ./tailwind.config.ts
COPY ./postcss.config.js ./postcss.config.js
COPY ./components.json ./components.json
COPY ./eslint.config.js ./eslint.config.js

ENV PORT=12000

# Build the frontend
# The output is typically in a 'dist' directory
RUN bun run build

# Stage 2: Setup the Python backend and serve the frontend
FROM python:3.12-slim AS backend

WORKDIR /app

# Install OS-level dependencies, Node.js, and npm
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    npm \
    unzip \
    openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# Copy frontend package configuration and install dependencies for npm run dev
COPY package.json ./
# If you have a package-lock.json, you might want to copy it too:
# COPY package-lock.json ./
RUN npm install

# Copy the rest of the frontend application source code for npm run dev
COPY ./public ./public
COPY ./src ./src
COPY ./vite.config.ts ./vite.config.ts
COPY ./tsconfig.json ./tsconfig.json
COPY ./tsconfig.app.json ./tsconfig.app.json
COPY ./tsconfig.node.json ./tsconfig.node.json
COPY ./index.html ./index.html
COPY ./tailwind.config.ts ./tailwind.config.ts
COPY ./postcss.config.js ./postcss.config.js
COPY ./components.json ./components.json
COPY ./eslint.config.js ./eslint.config.js


# Copy backend requirements first to leverage Docker cache
COPY FlaskBackend/requirements.txt ./FlaskBackend/requirements.txt
RUN pip install --no-cache-dir -r FlaskBackend/requirements.txt

# NLTK data download (optional, if your app needs it at runtime and can't download it then)
# If your app downloads these on first run, this step might not be strictly necessary here,
# but pre-downloading can make startup faster and more reliable in a container.
# RUN python -m nltk.downloader stopwords wordnet punkt averaged_perceptron_tagger
# Consider adding a script to handle NLTK downloads if they are extensive or conditional.

ENV NLTK_DATA /root/nltk_data
RUN mkdir -p $NLTK_DATA && \
    python -m nltk.downloader -d $NLTK_DATA stopwords wordnet punkt averaged_perceptron_tagger

# Copy the backend application code
COPY ./FlaskBackend ./FlaskBackend

# Copy the built frontend from the frontend-builder stage
# Assuming the Flask app is set up to serve static files from 'FlaskBackend/static/react_app'
RUN mkdir -p ./FlaskBackend/static/react_app
COPY --from=frontend-builder /app/dist ./FlaskBackend/static/react_app

# Set environment variables (if any are needed and not baked into the app)
# Example: ENV FLASK_APP=FlaskBackend/app.py
# ENV FLASK_RUN_HOST=0.0.0.0
# ENV FLASK_ENV=production
# The user prompt mentioned "without parameters from out", so critical env vars should be set here if not in the app.
# However, it's generally better to configure via Docker environment variables at runtime for flexibility.
# For now, I'll assume the app.py handles its own config or uses defaults.

ENV GOOGLE_APPLICATION_CREDENTIALS /app/FlaskBackend/nth-armor-453113-i4-d0ee56f72c64.json
ENV GEMINI_API_KEY "AIzaSyBeXj90uqORsY2IYzzaMUg_3ruWjbbnTN4"
ENV FLASK_SECRET_KEY "a9b2c1d4e7f0831a6b8c9d2e5f0123456789abcdef"
ENV FLASK_PORT=12001
ENV PORT=12000 
ENV FLASK_ENV="development"

# Expose ports
EXPOSE 12001 
EXPOSE 12000 

# Command to run the applications
# npm run dev will run the frontend dev server (e.g., Vite)
# The '--' ensures that --host and --port are passed to the script, not npm itself.
# The '&' runs npm run dev in the background.
CMD ["sh", "-c", "npm run dev -- --host 0.0.0.0 --port $PORT & python ./FlaskBackend/app.py"]
