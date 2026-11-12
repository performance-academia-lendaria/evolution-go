package user_service

import (
	"encoding/json"
	"reflect"
	"testing"

	"go.mau.fi/whatsmeow/types"
)

func TestBlocklistResponsePreservesPublicJSON(t *testing.T) {
	list := &types.Blocklist{DHash: "test-hash", Items: []types.BlocklistItem{
		{PN: types.NewJID("test-phone", types.DefaultUserServer), LID: types.NewJID("test-lid", types.HiddenUserServer), Active: true},
		{LID: types.NewJID("lid-only", types.HiddenUserServer), Active: true},
	}}
	data, err := json.Marshal(blocklistResponse(list))
	if err != nil {
		t.Fatal(err)
	}
	var got map[string]any
	if err := json.Unmarshal(data, &got); err != nil {
		t.Fatal(err)
	}
	want := map[string]any{"DHash": "test-hash", "JIDs": []any{"test-phone@s.whatsapp.net", "lid-only@lid"}}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("public blocklist JSON changed: got %s", data)
	}
}
