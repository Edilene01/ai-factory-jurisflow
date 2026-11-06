# Imagem fixada por digest de versão, pelo mesmo motivo das dependências: build
# reproduzível. A ADR-005 fixou a imagem do n8n depois que a divergência de
# versão quebrou o roteamento em produção.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY static/ ./static/

# Railway injeta PORT; o padrão serve para rodar local sem variável nenhuma.
ENV PORT=8080
EXPOSE 8080

# Sem --reload: recarregamento automático é ferramenta de desenvolvimento e em
# produção só acrescenta superfície.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
