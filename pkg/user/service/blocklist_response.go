package user_service

import "go.mau.fi/whatsmeow/types"

// Blocklist keeps the HTTP contract independent of the SDK's LID/PN item model.
type Blocklist struct {
	DHash string
	JIDs  []types.JID
}

func blocklistResponse(list *types.Blocklist) *Blocklist {
	if list == nil {
		return nil
	}
	response := &Blocklist{DHash: list.DHash}
	for _, item := range list.Items {
		jid := item.PN
		if jid.IsEmpty() {
			jid = item.LID
		}
		response.JIDs = append(response.JIDs, jid)
	}
	return response
}
