docker run -it --rm -v "$(pwd)/AI_pkg:/AI_pkg" --runtime nvidia --network pros_app_my_bridge_network  --env-file ./.env ghcr.io/otischung/pros_ai_image:0.0.0 /bin/bash
