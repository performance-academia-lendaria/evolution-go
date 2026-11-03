package main

import (
	"os"
	"regexp"
	"strings"
	"testing"
)

// The fork version combines the upstream base with the Academy's own sequence.
func TestForkVersionAndChangelog(t *testing.T) {
	data, err := os.ReadFile("../../VERSION")
	if err != nil {
		t.Fatal(err)
	}
	version := strings.TrimSuffix(string(data), "\n")
	number := `(0|[1-9][0-9]*)`
	pattern := `^` + number + `\.` + number + `\.` + number + `-` + number + `\.` + number + `\.` + number + `$`
	if !regexp.MustCompile(pattern).MatchString(version) {
		t.Fatalf("VERSION must use upstream-major.minor.patch-fork-major.minor.patch without leading zeros: %q", version)
	}
	changelog, err := os.ReadFile("../../CHANGELOG.md")
	if err != nil {
		t.Fatal(err)
	}
	if !regexp.MustCompile(`(?m)^## ` + regexp.QuoteMeta(version) + `(?:\s|$)`).Match(changelog) {
		t.Fatalf("CHANGELOG.md must contain an entry for VERSION %s", version)
	}
}
