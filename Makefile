# dev build load push

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