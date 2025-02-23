#!/bin/sh

echo "Rebuild FrontEnd and Restart Django."
CURRENT_DIR=$(cd $(dirname $0); pwd)
cd ${CURRENT_DIR}/../front || exit
npm run build

bash ${CURRENT_DIR}/startTestServer.sh