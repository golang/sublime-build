package good

import (
	"testing"
)

func TestRuneLen(t *testing.T) {
	cases := []struct {
		s          string
		byteLength int
		runeLength int
	}{
		{"résumé", 8, 6},
		{"résumé – new", 16, 12},
	}
	for _, c := range cases {
		if len(c.s) != c.byteLength {
			t.Errorf("len(%q) != %d", c.s, c.byteLength)
		}
		if RuneLen(c.s) != c.runeLength {
			t.Errorf("RuneLen(%q) != %d", c.s, c.runeLength)
		}
	}
}
