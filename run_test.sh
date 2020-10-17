#!/bin/bash

SKIP_INTERNAL_TEST=1
if [ "$#" -ge "1" ]; then
	SKIP_INTERNAL_TEST="$1"
fi

SKIP_INTERNAL_TEST=$SKIP_INTERNAL_TEST python -m pytest
