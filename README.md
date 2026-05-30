# train_checker

This repository serves as an exploration for a personal project. The main idea is to build a scheduler for checking recurrently trains and:
1. Save the tracking of the prices
2. Tell when the prices are low

For now, we are only evaluating the APIs for Madrid-Barcelona two-way travels.

## 🛠️ Build and run

Use the following commands to build the image and run the container:

```sh
docker build -t train_checker .
docker run --rm --name train_checker -v .:/app -t train_checker
```
