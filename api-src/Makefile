include .env
# ENV_VARS = $(shell sed -nr "s@^([A-Za-z_]+): (.+)@\1=\2@ p" env-vars-local.yaml)
ENV_VARS = $(shell cat .env)

env_setup:
	$(foreach v,$(ENV_VARS),$(eval export $(v)))

run_local: env_setup
	flask run