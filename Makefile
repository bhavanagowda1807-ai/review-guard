.PHONY: test build-frontend compile train-metadata train-fusion train-all verify deploy

test:
	python -m pytest backend/tests ml_service/tests

verify:
	python -m compileall backend ml_service
	python -m pytest backend/tests ml_service/tests
	cd frontend && npm run build

build-frontend:
	cd frontend && npm run build

deploy:
	docker compose up --build

train-text:
	cd ml_service && python train/train.py --module text --mlflow --mlflow-uri http://localhost:5000

train-image:
	cd ml_service && python train/train.py --module image --mlflow --mlflow-uri http://localhost:5000

train-metadata:
	cd ml_service && python train/train.py --module metadata --mlflow --mlflow-uri http://localhost:5000

train-fusion:
	cd ml_service && python train/train.py --module fusion --mlflow --mlflow-uri http://localhost:5000

train-all:
	cd ml_service && python ../scripts/train_all.sh
