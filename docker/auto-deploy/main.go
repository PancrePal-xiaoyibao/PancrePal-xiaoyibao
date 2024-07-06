package main

import (
	"fmt"
	"os"

	"github.com/peterwillcn/ai-lauch/libs"
)

func main() {
	container := libs.NewContainer()

	// 0
	templates, err := libs.ReadTemplate(container.TmplDir)
	if err != nil {
		fmt.Errorf("failed to parse templates: %w", err)
	}

	// 1
	err = os.MkdirAll(container.WorkDir, 0755)
	if err != nil {
		fmt.Printf("Error creating directory %s: %s\n", container.WorkDir, err)
	}

	// 2
	for _, maniFest := range container.ManiFests {
		libs.ApplyTemplate(container.WorkDir, templates, maniFest, container)
	}

	// 3
	libs.Start(container.WorkDir, container.ManiFests)

}
