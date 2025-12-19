FROM golang:1.21-alpine AS builder

WORKDIR /app

COPY go.mod ./
# RUN go mod download # We might not have go.sum yet, so maybe skip verify or generate it
# If we don't have go.sum, 'go mod download' might fail or warn. 
# We'll run 'go mod tidy' inside the container if needed or just copy source.

COPY . .
RUN go mod tidy
RUN go build -o iris-broker-service main.go

FROM alpine:3.18

WORKDIR /app
COPY --from=builder /app/iris-broker-service .

EXPOSE 8081

CMD ["./iris-broker-service"]
