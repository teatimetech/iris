# Use a lightweight Go base image for small containers
FROM golang:1.21-alpine AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

# Build the Go application binary
RUN CGO_ENABLED=0 GOOS=linux go build -o /iris-gateway main.go

# Final stage: Use a scratch or minimal image for security/size
FROM alpine:latest
RUN apk --no-cache add ca-certificates

WORKDIR /root/
COPY --from=builder /iris-gateway .

# Expose the port and set the entrypoint
EXPOSE 8080
CMD ["./iris-gateway"]
