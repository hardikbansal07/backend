FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH="/app:/app/calculation/calculation-main/src:/app/astroEngine-2.0/astroEngine-2.0"
ENV PYTHONUNBUFFERED=1

# Environment variables (Cloud Run does NOT read app.yaml env_variables)
ENV MONGO_URI="mongodb+srv://Astrocare7:Astrocare7337@cluster0.ydviwil.mongodb.net/"
ENV DB_NAME="Astrocare7"
ENV GEMINI_API_KEY="AIzaSyBuu5Pw3aq38MIuTA24qu4M1sPhDfdMEc0"
ENV SECRET_KEY="9bc5f5ce2dc60b380533703ed545b71a40b807d5269a41358eb0e6a6ebe2342e"
ENV GOOGLE_CLIENT_ID="209987574410-rpfj1o45f6igoem4fnjiefmhjmbjohf3.apps.googleusercontent.com"
ENV GOOGLE_CLIENT_SECRET="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"
ENV GOOGLE_REDIRECT_URI="https://ai-astrology-481805.as.r.appspot.com/api/v1/auth/google/callback"
ENV FACEBOOK_APP_ID="4171301276441086"
ENV FACEBOOK_APP_SECRET="dda90c714ffa19271386b4f1b9d854d4"
ENV GEMINI_MODEL="gemini-2.5-flash-lite"
ENV DATABASE_URL="mongodb+srv://Astrocare7:Astrocare7337@cluster0.ydviwil.mongodb.net/?appName=Cluster0"
ENV GOOGLE_CLOUD_PROJECT="astro-491617"
ENV GOOGLE_CLOUD_LOCATION="asia-south1"
ENV SUPABASE_URL="https://dmlbtfrdrklwytakzzcd.supabase.co"
ENV SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRtbGJ0ZnJkcmtsd3l0YWt6emNkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTIzMTkwOCwiZXhwIjoyMDkwODA3OTA4fQ.GMNyy1vGQmRAd7NmuKcoEuI1SoiAB8iF5Jt51OYt0wk"
ENV BASE_URL="https://backend-209987574410.asia-south1.run.app"

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1"]
