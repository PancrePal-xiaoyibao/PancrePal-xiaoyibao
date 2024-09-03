#!/bin/sh

set -e

docker run -it  -d --init \
    --name wxkf-api \
    --network=host \
    -v $(pwd)/secret.yml:/app/secret.yml:ro \
    -v $(pwd)/agents.yml:/app/agents.yml:ro \
    -v /etc/localtime:/etc/localtime:ro \
    --restart on-failure \
    dockerproxy.cn/vinlic/wxkf-api:latest

echo "Startup completed!"

docker logs -f wxkf-api