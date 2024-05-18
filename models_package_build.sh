#!/bin/sh

rm -rf artifacts/*
rm -rf backend/gagm-base/dist/*
mkdir -p backend/gagm-base/dist
cd ./gagm-base
python -m build --wheel
cp dist/*.whl ../artifacts
cp dist/*.whl ../backend/gagm-base/dist
cd ..

if [ "$1" = "--install-on-backend-venv" ] || [ "$1" = "-I" ]; then
    source "$2/bin/activate"
    pip install --force-reinstall artifacts/*.whl
    deactivate
fi
