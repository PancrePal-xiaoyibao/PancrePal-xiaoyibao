FLAGS = -ldflags '-extldflags "-static"'

all:
	go build $(FLAGS) -o launch main.go
	GOOS=linux GOARCH=amd64 go build $(FLAGS) -o launch-amd64 main.go