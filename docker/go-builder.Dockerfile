FROM golang:1.21-alpine

WORKDIR /workspace

# Install build dependencies
RUN apk add --no-cache git make

CMD ["sh"]

