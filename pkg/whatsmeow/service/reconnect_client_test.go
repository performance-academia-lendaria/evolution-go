package whatsmeow_service

import (
	"context"
	"errors"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/evolution-foundation/evolution-go/pkg/config"
	instance_model "github.com/evolution-foundation/evolution-go/pkg/instance/model"
	instance_repository "github.com/evolution-foundation/evolution-go/pkg/instance/repository"
	logger_wrapper "github.com/evolution-foundation/evolution-go/pkg/logger"
	"go.mau.fi/whatsmeow"
	"go.mau.fi/whatsmeow/proto/waCompanionReg"
	"go.mau.fi/whatsmeow/store"
	"go.mau.fi/whatsmeow/types/events"
	"google.golang.org/protobuf/proto"
)

type reconnectTestRepository struct {
	instance_repository.InstanceRepository
	get func(string) (*instance_model.Instance, error)
}

func (r *reconnectTestRepository) GetInstanceByID(id string) (*instance_model.Instance, error) {
	return r.get(id)
}

func readyForReconnectTest(t *testing.T) {
	t.Helper()
	oldVersion := store.GetWAVersion()
	oldProps := proto.Clone(store.DeviceProps).(*waCompanionReg.DeviceProps)
	resetWAVersionInitializationForTest()
	t.Cleanup(func() {
		store.SetWAVersion(oldVersion)
		store.DeviceProps = oldProps
		resetWAVersionInitializationForTest()
	})
	if err := InitializeWAVersion(&config.Config{WhatsappVersionMajor: 2, WhatsappVersionMinor: 3000, WhatsappVersionPatch: 1052878631}); err != nil {
		t.Fatal(err)
	}
}

func TestReconnectDisconnectsClosedClientAndRemovesHandler(t *testing.T) {
	readyForReconnectTest(t)
	client := whatsmeow.NewClient(&store.Device{}, nil)
	var handlerCalls atomic.Int32
	handlerID := client.AddEventHandler(func(any) { handlerCalls.Add(1) })
	if client.IsConnected() || client.DangerousInternals().IsExpectedDisconnect() {
		t.Fatal("fixture must start as an unexpectedly disconnected client")
	}
	errStop := errors.New("stop before creating replacement")
	cfg := &config.Config{LogDirectory: t.TempDir()}
	w := &whatsmeowService{
		instanceRepository: &reconnectTestRepository{get: func(string) (*instance_model.Instance, error) { return nil, errStop }},
		clientPointer:      map[string]*whatsmeow.Client{"test": client},
		myClientPointer:    map[string]*MyClient{"test": {WAClient: client, eventHandlerID: handlerID}},
		loggerWrapper:      logger_wrapper.NewLoggerManager(cfg),
	}
	if err := w.ReconnectClient("test"); err == nil || !strings.Contains(err.Error(), errStop.Error()) {
		t.Fatalf("expected controlled stop after cleanup, got %v", err)
	}
	// Disconnect is meaningful even after the socket closes: the current SDK
	// marks the close expected and drains the old connection's handler queue.
	if !client.DangerousInternals().IsExpectedDisconnect() {
		t.Error("old client was not explicitly disconnected after its socket closed")
	}
	client.DangerousInternals().DispatchEvent(&events.Archive{})
	if handlerCalls.Load() != 0 {
		t.Error("old event handler remains registered")
	}
}

func TestReconnectCoalescesConcurrentRequests(t *testing.T) {
	readyForReconnectTest(t)
	var calls atomic.Int32
	entered := make(chan struct{}, 8)
	release := make(chan struct{})
	var once sync.Once
	unblock := func() { once.Do(func() { close(release) }) }
	t.Cleanup(unblock)
	errStop := errors.New("controlled repository stop")
	repo := &reconnectTestRepository{get: func(string) (*instance_model.Instance, error) {
		calls.Add(1)
		entered <- struct{}{}
		<-release
		return nil, errStop
	}}
	cfg := &config.Config{LogDirectory: t.TempDir()}
	w := &whatsmeowService{instanceRepository: repo, loggerWrapper: logger_wrapper.NewLoggerManager(cfg)}
	results := make(chan error, 2)
	go func() { results <- w.ReconnectClient("same-device") }()
	select {
	case <-entered:
	case <-time.After(2 * time.Second):
		t.Fatal("first reconnect did not enter repository barrier")
	}
	secondStarted := make(chan struct{})
	go func() {
		close(secondStarted)
		results <- w.ReconnectClient("same-device")
	}()
	<-secondStarted
	select {
	case <-entered:
		t.Error("second reconnect entered cleanup while the first was still active")
	case <-time.After(150 * time.Millisecond):
	}
	unblock()
	for range 2 {
		select {
		case err := <-results:
			if err == nil || !strings.Contains(err.Error(), errStop.Error()) {
				t.Errorf("callers must share the reconnect result, got %v", err)
			}
		case <-time.After(2 * time.Second):
			t.Fatal("reconnect caller did not finish")
		}
	}
	// One reconnect does the cache lookup and instance lookup, then stops.
	if got := calls.Load(); got != 2 {
		t.Fatalf("expected one cleanup/start attempt (2 lookups), got %d lookups", got)
	}
}

func TestReconnectWaitsForPreviousWorkerToStop(t *testing.T) {
	readyForReconnectTest(t)
	ctx, cancel := context.WithCancel(context.Background())
	stopped := make(chan struct{})
	go func() {
		<-ctx.Done()
		close(stopped)
	}()
	t.Cleanup(func() {
		cancel()
		<-stopped
	})
	errStop := errors.New("stop before replacement starts")
	repo := &reconnectTestRepository{get: func(string) (*instance_model.Instance, error) {
		select {
		case <-stopped:
		default:
			t.Error("replacement bookkeeping started while the previous worker was alive")
		}
		return nil, errStop
	}}
	client := whatsmeow.NewClient(&store.Device{}, nil)
	cfg := &config.Config{LogDirectory: t.TempDir()}
	w := &whatsmeowService{
		instanceRepository: repo,
		clientPointer:      map[string]*whatsmeow.Client{"test": client},
		myClientPointer: map[string]*MyClient{"test": {
			WAClient: client, ctx: ctx, cancel: cancel, stopped: stopped,
		}},
		loggerWrapper: logger_wrapper.NewLoggerManager(cfg),
	}
	if err := w.ReconnectClient("test"); err == nil || !strings.Contains(err.Error(), errStop.Error()) {
		t.Fatalf("expected controlled stop after old worker shutdown, got %v", err)
	}
	if ctx.Err() == nil {
		t.Error("previous worker context was not canceled")
	}
}

func TestStaleDisconnectedDoesNotRestartReplacement(t *testing.T) {
	readyForReconnectTest(t)
	previous := whatsmeow.NewClient(&store.Device{}, nil)
	current := whatsmeow.NewClient(&store.Device{}, nil)
	var handlerCalls, repositoryCalls atomic.Int32
	current.AddEventHandler(func(any) { handlerCalls.Add(1) })
	cfg := &config.Config{LogDirectory: t.TempDir()}
	w := &whatsmeowService{
		clientPointer: map[string]*whatsmeow.Client{"test": current},
		instanceRepository: &reconnectTestRepository{get: func(string) (*instance_model.Instance, error) {
			repositoryCalls.Add(1)
			return nil, errors.New("stale callback must not reach replacement bookkeeping")
		}},
		loggerWrapper: logger_wrapper.NewLoggerManager(cfg),
	}
	if err := w.reconnectClient("test", previous); err != nil {
		t.Errorf("stale disconnect should be ignored, got %v", err)
	}
	if repositoryCalls.Load() != 0 || current.DangerousInternals().IsExpectedDisconnect() {
		t.Error("stale callback retired the replacement client")
	}
	current.DangerousInternals().DispatchEvent(&events.Archive{})
	if handlerCalls.Load() != 1 {
		t.Error("replacement event handler was removed by a stale callback")
	}
}

type qrTimeoutBarrierRepository struct {
	instance_repository.InstanceRepository
	entered chan struct{}
	release chan struct{}
}

func (r *qrTimeoutBarrierRepository) UpdateQrcode(string, string) error {
	close(r.entered)
	<-r.release
	return nil
}

func TestCanceledQRTimeoutCannotStopReplacement(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	t.Cleanup(cancel)
	oldKill := make(chan bool)
	replacementKill := make(chan bool, 1)
	channels := map[string]chan bool{"test": oldKill}
	repo := &qrTimeoutBarrierRepository{entered: make(chan struct{}), release: make(chan struct{})}
	var once sync.Once
	release := func() { once.Do(func() { close(repo.release) }) }
	t.Cleanup(release)
	cfg := &config.Config{LogDirectory: t.TempDir()}
	mycli := &MyClient{
		ctx: ctx, killSignal: oldKill, killChannel: channels, userID: "test",
		Instance:           &instance_model.Instance{Id: "test", Name: "QR regression"},
		instanceRepository: repo,
		config:             cfg,
		loggerWrapper:      logger_wrapper.NewLoggerManager(cfg),
		service:            &archiveCaptureService{calls: make(chan archiveWebhookCall, 1)},
	}
	done := make(chan struct{})
	go func() {
		defer close(done)
		mycli.teardownQR("", false)
	}()
	select {
	case <-repo.entered:
	case <-time.After(2 * time.Second):
		t.Fatal("old QR timeout did not reach barrier")
	}
	cancel()
	// The replacement publishes its channel while the old DB operation finishes.
	channels["test"] = replacementKill
	release()
	select {
	case <-done:
	case <-time.After(2 * time.Second):
		t.Fatal("canceled QR timeout did not finish")
	}
	if len(replacementKill) != 0 {
		t.Fatal("old QR timeout sent a stop signal to the replacement")
	}
}
