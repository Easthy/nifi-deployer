#!/bin/bash

set -e

build() {
    NAME=$1
    IMAGE=local-$NAME
    cd $([ -z "$2" ] && echo "./$NAME" || echo "$2")
    echo '--------------------------' building $IMAGE in $(pwd)
    docker build -t $IMAGE .
    cd -
}

build toolkit
build nifi
build nifi-registry
