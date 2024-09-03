#!/bin/sh

set -e

docker stop wxkf-api
docker rm wxkf-api

echo "Shudown completed!"
