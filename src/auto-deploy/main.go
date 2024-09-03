package main

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/peterwillcn/ai-launch/libs"
)

func main() {
	container := libs.NewContainer()
	os.MkdirAll(filepath.Join(container.WorkDir, container.DataDir), 0755)
	libs.MakeConfig(container)
	switch container.Operation {
	case "start":
		libs.Start(container)
	case "stop":
		libs.Stop(container)
	case "backup":
		libs.Backup(container)
	default:
		fmt.Printf("Unknown operation: [ %s ], \nexample: [ ./launch -o start (stop, restart) ] \n", container.Operation)
	}
}
