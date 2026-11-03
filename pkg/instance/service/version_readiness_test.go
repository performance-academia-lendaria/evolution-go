package instance_service

import (
	"errors"
	"testing"

	instance_model "github.com/evolution-foundation/evolution-go/pkg/instance/model"
	whatsmeow_service "github.com/evolution-foundation/evolution-go/pkg/whatsmeow/service"
)

func TestConnectionsFailFastWhenVersionIsNotReady(t *testing.T) {
	if whatsmeow_service.WAVersionReady() {
		t.Fatal("test expects a fresh process without initialized WhatsApp version")
	}
	svc := instances{}
	_, _, _, err := svc.Connect(&ConnectStruct{}, &instance_model.Instance{})
	if !errors.Is(err, whatsmeow_service.ErrWAVersionNotReady) {
		t.Fatalf("connect should fail immediately while version is unavailable: %v", err)
	}
	if err := svc.ForceReconnect("instance", "number"); !errors.Is(err, whatsmeow_service.ErrWAVersionNotReady) {
		t.Fatalf("force reconnect should fail immediately while version is unavailable: %v", err)
	}
}
