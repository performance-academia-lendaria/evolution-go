package user_service

import (
	"context"
	"testing"

	"go.mau.fi/whatsmeow/store"
	"go.mau.fi/whatsmeow/types"
)

type checkLIDStore struct {
	store.LIDStore
	get func(types.JID) (types.JID, error)
}

func (s checkLIDStore) GetLIDForPN(_ context.Context, jid types.JID) (types.JID, error) {
	return s.get(jid)
}

func TestCheckUserPreservesPhoneIdentityWithLIDResponse(t *testing.T) {
	pn := types.NewJID("test-phone", types.DefaultUserServer)
	lid := types.NewJID("test-lid", types.HiddenUserServer)
	for _, lidAddressed := range []bool{true, false} {
		t.Run(map[bool]string{true: "lid_response", false: "legacy_pn_response"}[lidAddressed], func(t *testing.T) {
			item := types.IsOnWhatsAppResponse{Query: "test-query", IsIn: true, JID: pn}
			if lidAddressed {
				item.JID = lid
				item.PhoneNumber = pn
			}
			calls := 0
			lookup := checkLIDStore{get: func(jid types.JID) (types.JID, error) {
				calls++
				if jid != pn {
					t.Errorf("LID store received non-phone JID %s", jid)
				}
				return lid, nil
			}}
			result, retry := mapCheckUserResponses([]types.IsOnWhatsAppResponse{item}, lookup, true)
			if retry || len(result.Users) != 1 {
				t.Fatal("positive check result was lost")
			}
			user := result.Users[0]
			if user.JID != pn.String() || user.RemoteJID != pn.String() || user.LID == nil || *user.LID != lid.String() {
				t.Fatalf("phone/LID HTTP contract changed: %+v", user)
			}
			if lidAddressed && calls != 0 {
				t.Fatal("SDK supplied LID but response mapper queried PN-only lookup")
			}
		})
	}
}

func TestCheckUserNotFoundKeepsQueryAndRetry(t *testing.T) {
	result, retry := mapCheckUserResponses([]types.IsOnWhatsAppResponse{{Query: "test-query"}}, nil, true)
	if !retry || len(result.Users) != 1 || result.Users[0].RemoteJID != "test-query" || result.Users[0].LID != nil {
		t.Fatal("missing-user query/retry behavior changed")
	}
}
