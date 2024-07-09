default:
  @just --list

# Docker containers on macOS
# brew install --cask docker

# Define default values for parameters

image_name := "app"
tag := "latest"
container_name := "app_container"
host_port := "8080"
container_port := "8080"
dockerfile := "Dockerfile"
build_context := "."

# Commands

update-st-config:
    streamlit config show > .streamlit/config.toml

app app_name="":
    streamlit run {{app_name}} --server.address=localhost

# Export pyproject.toml to requirements.txt
reqs:
    pdm export --o requirements.txt --without-hashes --prod


# Docker

dbuild:
    docker build -t {{image_name}}:{{tag}} -f {{dockerfile}} {{build_context}}

drun:
    docker run --name {{container_name}} -p {{host_port}}:{{container_port}} -d {{image_name}}:{{tag}}

dstop:
    docker stop {{container_name}}

dremove:
    docker rm {{container_name}}

dlogs:
    docker logs {{container_name}}

dshell:
    docker exec -it {{container_name}} /bin/sh

dpush:
    docker push {{image_name}}:{{tag}}

dpull:
    docker pull {{image_name}}:{{tag}}
