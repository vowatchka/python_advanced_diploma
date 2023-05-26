# Create help description:
# https://gist.github.com/prwhite/8168133?permalink_comment_id=2833138#gistcomment-2833138

.PHONY: help
help:
	@awk 'BEGIN {FS = ":.*#"; printf "Usage: make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?#/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Vagrant
.PHONY: vm-up
vm-up: # starts the vagrant machine
	vagrant up

.PHONY: vm-down
vm-down: # stops the vagrant machine
	vagrant halt

.PHONY: vm-provision
vm-provision: # provisions the vagrant machine
	vagrant provision

.PHONY: up-provision
vm-up-provision: # starts and provisions the vagrant machine
	vagrant up --provision

.PHONY: vm-connect
vm-connect: # connects to machine via SSH
	vagrant ssh


##@ Docker Compose
.PHONY: up
up: # create and start containers
	docker-compose up -d

.PHONY: down
down: # stop and remove containers, networks
	docker-compose down

.PHONY: rebuild
rebuild: # rebuild and recreate containers
	docker-compose up -d --build

.PHONY: test
test: # run tests
	docker-compose exec api pytest -v

.PHONY: lint
lint: # run linting
	docker-compose exec api flake8 --verbose --color always ./tweetty

.PHONY: migrate
migrate: # apply migrations
	docker-compose exec api alembic upgrade head

.PHONY: app-logs
app-logs: # show application logs. Use ARGS for additional arguments
	docker-compose logs api $(ARGS)

