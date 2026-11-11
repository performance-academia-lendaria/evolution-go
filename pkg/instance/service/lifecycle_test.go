package instance_service

import (
	"errors"
	"os"
	"os/exec"
	"testing"

	"github.com/evolution-foundation/evolution-go/pkg/config"
	instance_model "github.com/evolution-foundation/evolution-go/pkg/instance/model"
	instance_repository "github.com/evolution-foundation/evolution-go/pkg/instance/repository"
	whatsmeow_service "github.com/evolution-foundation/evolution-go/pkg/whatsmeow/service"
	"go.mau.fi/whatsmeow"
	"go.mau.fi/whatsmeow/store"
)

type lifecycleRepository struct {
	instance_repository.InstanceRepository
}

func (*lifecycleRepository) GetInstanceByID(id string) (*instance_model.Instance, error) {
	return &instance_model.Instance{Id: id}, nil
}
func (*lifecycleRepository) Delete(string) error { return nil }

type lifecycleService struct {
	whatsmeow_service.WhatsmeowService
	clear        func() error
	reconnect    func() error
	directStarts int
}

func (s *lifecycleService) ClearInstanceCache(string, string) error   { return s.clear() }
func (s *lifecycleService) ForceUpdateJid(string, string) error       { return nil }
func (s *lifecycleService) ReconnectClient(string) error              { return s.reconnect() }
func (s *lifecycleService) StartClient(*whatsmeow_service.ClientData) { s.directStarts++ }

func TestDeleteRetiresWorkerBeforeDiscardingItsChannel(t *testing.T) {
	kill := make(chan bool)
	service := &lifecycleService{clear: func() error {
		select {
		case _, open := <-kill:
			if !open {
				t.Error("deletion closed the callback's channel before retirement")
			}
		default:
		}
		return nil
	}}
	svc := instances{instanceRepository: &lifecycleRepository{}, whatsmeowService: service,
		killChannel: map[string]chan bool{"test": kill}}
	if err := svc.Delete("test"); err != nil {
		t.Fatal(err)
	}
}

func TestForceReconnectUsesSerializedLifecycle(t *testing.T) {
	// Version initialization is process-global; keep the readiness test's fresh
	// process contract intact by running this initialized case in its own process.
	if os.Getenv("EVOSYNC_FORCE_RECONNECT_CHILD") != "1" {
		cmd := exec.Command(os.Args[0], "-test.run=^TestForceReconnectUsesSerializedLifecycle$")
		cmd.Env = append(os.Environ(), "EVOSYNC_FORCE_RECONNECT_CHILD=1")
		if output, err := cmd.CombinedOutput(); err != nil {
			t.Fatalf("initialized lifecycle test: %v\n%s", err, output)
		}
		return
	}
	if err := whatsmeow_service.InitializeWAVersion(&config.Config{WhatsappVersionMajor: 2, WhatsappVersionMinor: 3000, WhatsappVersionPatch: 1052878631}); err != nil {
		t.Fatal(err)
	}
	want := errors.New("serialized lifecycle reached")
	service := &lifecycleService{reconnect: func() error { return want }}
	svc := instances{instanceRepository: &lifecycleRepository{}, whatsmeowService: service, config: &config.Config{},
		clientPointer: map[string]*whatsmeow.Client{"test": whatsmeow.NewClient(&store.Device{}, nil)},
		killChannel:   map[string]chan bool{"test": make(chan bool, 1)}}
	err := svc.ForceReconnect("test", "synthetic")
	if !errors.Is(err, want) || service.directStarts != 0 {
		t.Fatalf("force reconnect bypassed serialized retirement: error=%v direct_starts=%d", err, service.directStarts)
	}
}
