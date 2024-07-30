FLAGS = -ldflags '-extldflags "-static"'

all:
	go build $(FLAGS) -o launch main.go

amd64:
	GOOS=linux GOARCH=amd64 go build $(FLAGS) -o launch main.go
