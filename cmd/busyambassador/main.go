// Ambassador combines the various Golang binaries used in the Ambassador
// container, dispatching on os.Args[0] like BusyBox. Note that the
// capabilities_wrapper binary is _not_ included here. That one has special
// permissions magic applied to it that is not appropriate for these other
// binaries.
package main

import (
	"github.com/datawire/ambassador/v2/pkg/busy"
	"github.com/datawire/ambassador/v2/pkg/environment"

	amb_agent "github.com/datawire/ambassador/v2/cmd/agent"
	"github.com/datawire/ambassador/v2/cmd/ambex"
	"github.com/datawire/ambassador/v2/cmd/entrypoint"
	"github.com/datawire/ambassador/v2/cmd/kubestatus"
	"github.com/datawire/ambassador/v2/cmd/reproducer"
	"github.com/datawire/ambassador/v2/cmd/watt"
)

// Version is inserted at build-time using --ldflags -X
var Version = "(unknown version)"

func noop() {}

func main() {
	busy.Main("busyambassador", "Ambassador", Version, map[string]busy.Command{
		"ambex":      {Setup: environment.EnvironmentSetupEntrypoint, Run: ambex.Main},
		"watt":       {Setup: environment.EnvironmentSetupEntrypoint, Run: watt.Main},
		"kubestatus": {Setup: environment.EnvironmentSetupEntrypoint, Run: kubestatus.Main},
		"entrypoint": {Setup: noop, Run: entrypoint.Main},
		"reproducer": {Setup: noop, Run: reproducer.Main},
		"agent":      {Setup: environment.EnvironmentSetupEntrypoint, Run: amb_agent.Main},
	})
}
