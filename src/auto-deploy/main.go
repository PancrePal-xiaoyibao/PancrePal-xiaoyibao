
import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/peterwillcn/ai-launch/libs"
	"github.com/schollz/progressbar/v3"
)

func main() {
	container := libs.NewContainer()
	fmt.Printf("Creating directory: %s\n", filepath.Join(container.WorkDir, container.DataDir))
	err := os.MkdirAll(filepath.Join(container.WorkDir, container.DataDir), 0755)
	if err != nil {
		fmt.Printf("Error creating directory: %v\n", err)
		return
	}

	fmt.Println("Generating configuration...")
	libs.MakeConfig(container)

	fmt.Printf("Operation: %s\n", container.Operation)
	var bar *progressbar.ProgressBar
	switch container.Operation {
	case "start":
		fmt.Println("Starting container...")
		bar = progressbar.NewOptions(100,
			progressbar.OptionEnableColorCodes(true),
			progressbar.OptionShowCount(),
			progressbar.OptionShowIts(),
			progressbar.OptionSetDescription("[cyan]Starting container[reset]"),
			progressbar.OptionSetTheme(progressbar.Theme{
				Saucer:        "[green]=[reset]",
				SaucerHead:    "[green]>[reset]",
				SaucerPadding: " ",
				BarStart:      "[",
				BarEnd:        "]",
			}),
		)
		err = libs.Start(container, bar)
	case "stop":
		fmt.Println("Stopping container...")
		bar = progressbar.NewOptions(100,
			progressbar.OptionEnableColorCodes(true),
			progressbar.OptionShowCount(),
			progressbar.OptionShowIts(),
			progressbar.OptionSetDescription("[red]Stopping container[reset]"),
			progressbar.OptionSetTheme(progressbar.Theme{
				Saucer:        "[red]=[reset]",
				SaucerHead:    "[red]>[reset]",
				SaucerPadding: " ",
				BarStart:      "[",
				BarEnd:        "]",
			}),
		)
		err = libs.Stop(container, bar)
	case "backup":
		fmt.Println("Backing up container...")
		bar = progressbar.NewOptions(100,
			progressbar.OptionEnableColorCodes(true),
			progressbar.OptionShowCount(),
			progressbar.OptionShowIts(),
			progressbar.OptionSetDescription("[yellow]Backing up container[reset]"),
			progressbar.OptionSetTheme(progressbar.Theme{
				Saucer:        "[yellow]=[reset]",
				SaucerHead:    "[yellow]>[reset]",
				SaucerPadding: " ",
				BarStart:      "[",
				BarEnd:        "]",
			}),
		)
		err = libs.Backup(container, bar)
	default:
		fmt.Printf("Unknown operation: [ %s ], \nexample: [ ./launch -o start (stop, restart) ] \n", container.Operation)
		return
	}

	if err != nil {
		fmt.Printf("Error during operation: %v\n", err)
		return
	}

	fmt.Println("Operation completed successfully.")
}
