auto-deploy
=========

## Introduction

Convenient and quick setup of AI system, one key deployment.

## Build and run step by step

### 1. Ubuntu Prerequisites

Make sure your ubuntu version is 22.04 or later.

```bash
$ cat /etc/issue
Ubuntu 22.04 LTS
```

Install Git and Docker.

```bash
$ sudo apt install -y git golang-go docker.io docker-compose
```

### 2. Clone source code
Make sure you are in the working folder.

```bash
$ git clone https://github.com/PancrePal-xiaoyibao/PancrePal-xiaoyibao.git
```

If clone works successfully, you should see folder structure like docker/auto-deploy

```bash
cat docker/auto-deploy/README.md
```

### 3. Make

Build the lauch.
```bash
$ cd docker/auto-deploy
$ go mod tidy
$ make amd64
```
If you did not see any error message, congratulations, you can find the executable file lauch in the bin directory.
```bash
ls -l bin/lauch
```

### 4. Configure

Modify based on default (deploy.json) configuration.

| Syntax      |                  Description                   | default value |
| :---        |:----------------------------------------------:|--------------:|
| WorkDir      | The deployment main directory of the project   |   ./run |
| TmplDir   |         Deployment template directory          |      ./tmpl |
| ManiFests      |              Deployment Manifests              |   "api", "gpt", "ngx" |
| ImageAPI   |             one-api container name             |      justsong/one-api:latest |
| ImageGPT      |             fastGPT container name             |   ghcr.io/labring/fastgpt:v4.6.4 |
| BaseURL   |           3rd ai interface base url            |      http://localhost:3600/v1 |
| ApiKey      |              3rd ai interface key              |   1234567890 |
| RootKey   |              one-api root api key              |      0987654321 |
| DbUser      |               database username                |   username |
| DbPass   |                databse password                |      password |
| DataDir      |             System Data directory              |   ./data |

```json
{
  "WorkDir":    "./run",
  "TmplDir":    "./tmpl",
  "ManiFests":  ["api", "gpt", "ngx"],
  "ImageAPI":   "justsong/one-api:latest",
  "ImageGPT":   "ghcr.io/labring/fastgpt:v4.6.4",
  "BaseURL":    "http://localhost:3600/v1",
  "ApiKey":     "1234567890",
  "RootKey":    "0987654321",
  "DbUser":     "username",
  "DbPass":     "password",
  "DataDir":    "./data"
}
```

### 5. Run the lauch start auto deploy

Run the lauch.
```bash
$ bin/lauch
```

## Contribution

We welcome contributions to the Project.

## Acknowledgments

A sincere thank you to all teams and projects that we rely on directly or indirectly.

## License

This project is licensed under the terms of the MIT license
