package whatsmeow_service

import (
	"encoding/json"
	"testing"
	"time"

	"github.com/evolution-foundation/evolution-go/pkg/config"
	instance_model "github.com/evolution-foundation/evolution-go/pkg/instance/model"
	logger_wrapper "github.com/evolution-foundation/evolution-go/pkg/logger"
	"go.mau.fi/whatsmeow/proto/waSyncAction"
	"go.mau.fi/whatsmeow/types"
	"go.mau.fi/whatsmeow/types/events"
	"google.golang.org/protobuf/proto"
)

type archiveWebhookCall struct {
	queue      string
	instanceID string
	payload    []byte
}

type archiveCaptureService struct {
	WhatsmeowService
	calls chan archiveWebhookCall
}

func (s *archiveCaptureService) CallWebhook(instance *instance_model.Instance, queue string, payload []byte) {
	s.calls <- archiveWebhookCall{queue: queue, instanceID: instance.Id, payload: append([]byte(nil), payload...)}
}

func TestArchiveEventDispatchesTypedPayload(t *testing.T) {
	for _, tc := range []struct {
		name     string
		action   *waSyncAction.ArchiveChatAction
		fullSync bool
	}{
		{name: "archive", action: &waSyncAction.ArchiveChatAction{Archived: proto.Bool(true)}},
		{name: "unarchive_full_sync", action: &waSyncAction.ArchiveChatAction{Archived: proto.Bool(false)}, fullSync: true},
		{name: "missing_action"},
	} {
		t.Run(tc.name, func(t *testing.T) {
			cfg := &config.Config{LogDirectory: t.TempDir()}
			capture := &archiveCaptureService{calls: make(chan archiveWebhookCall, 1)}
			instance := &instance_model.Instance{Id: "archive-test-instance", Name: "Archive regression"}
			client := &MyClient{
				service:       capture,
				Instance:      instance,
				userID:        instance.Id,
				config:        cfg,
				loggerWrapper: logger_wrapper.NewLoggerManager(cfg),
			}
			evt := &events.Archive{
				JID:          types.JID{User: "archive-test", Server: types.DefaultUserServer},
				Timestamp:    time.Date(2026, time.November, 11, 9, 0, 0, 0, time.UTC),
				Action:       tc.action,
				FromFullSync: tc.fullSync,
			}
			// Use the actual event handler: checking a serializer alone would miss
			// the type assertion on the raw *events.Archive value.
			client.myEventHandler(evt)

			select {
			case call := <-capture.calls:
				if call.queue != instance.Id+".archive" || call.instanceID != instance.Id {
					t.Fatalf("unexpected archive dispatch: queue=%q instance=%q", call.queue, call.instanceID)
				}
				var payload struct {
					Event        string `json:"event"`
					InstanceID   string `json:"instanceId"`
					InstanceName string `json:"instanceName"`
					Data         struct {
						JID          string
						Timestamp    time.Time
						Action       *waSyncAction.ArchiveChatAction
						FromFullSync bool
					} `json:"data"`
				}
				if err := json.Unmarshal(call.payload, &payload); err != nil {
					t.Fatal(err)
				}
				if payload.Event != "Archive" || payload.InstanceID != instance.Id || payload.InstanceName != instance.Name {
					t.Fatalf("archive envelope was not preserved: %+v", payload)
				}
				if payload.Data.JID != evt.JID.String() || !payload.Data.Timestamp.Equal(evt.Timestamp) ||
					payload.Data.FromFullSync != evt.FromFullSync || !proto.Equal(payload.Data.Action, evt.Action) {
					t.Fatalf("archive action was not preserved: %+v", payload.Data)
				}
			case <-time.After(2 * time.Second):
				t.Fatal("archive event did not reach webhook dispatch")
			}
		})
	}
}
