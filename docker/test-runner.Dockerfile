FROM alpine:latest

# Install testing tools
RUN apk add --no-cache \
    bash \
    curl \
    kubectl \
    jq \
    dos2unix

WORKDIR /workspace

CMD ["/bin/bash"]
