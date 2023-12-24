# dev build load push

init:
	yarn install
	cp .env.tpl .env
	cp ./docs/.vuepress/config.js.tpl ./docs/.vuepress/config.js

dev:
	yarn dev
 
build:
	yarn build

load:
	python process_siyuan_export.py load -f $f

gen-all:
	python process_siyuan_export.py gen-all

push:
	pass