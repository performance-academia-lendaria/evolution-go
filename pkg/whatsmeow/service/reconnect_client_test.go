package whatsmeow_service

import (
	"context"
	"errors"
	"fmt"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/evolution-foundation/evolution-go/pkg/config"
	instance_model "github.com/evolution-foundation/evolution-go/pkg/instance/model"
	instance_repository "github.com/evolution-foundation/evolution-go/pkg/instance/repository"
	logger_wrapper "github.com/evolution-foundation/evolution-go/pkg/logger"
	"github.com/patrickmn/go-cache"
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

type logoutBarrierRepository struct {
	instance_repository.InstanceRepository
	entered chan struct{}
	release chan struct{}
}

func (r *logoutBarrierRepository) UpdateConnected(string, bool, string) error {
	close(r.entered)
	<-r.release
	return nil
}

func TestCanceledLogoutHandlerDoesNotBlockRetirement(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	kill := make(chan bool)
	repo := &logoutBarrierRepository{entered: make(chan struct{}), release: make(chan struct{})}
	cfg := &config.Config{LogDirectory: t.TempDir()}
	mycli := &MyClient{
		ctx: ctx, killSignal: kill, killChannel: map[string]chan bool{"test": kill}, userID: "test",
		Instance: &instance_model.Instance{Id: "test"}, instanceRepository: repo, config: cfg,
		userInfoCache: cache.New(time.Minute, time.Minute), loggerWrapper: logger_wrapper.NewLoggerManager(cfg),
		service: &archiveCaptureService{calls: make(chan archiveWebhookCall, 2)},
	}
	client := whatsmeow.NewClient(&store.Device{}, nil)
	client.AddEventHandler(mycli.myEventHandler)
	dispatched := make(chan struct{})
	go func() {
		client.DangerousInternals().DispatchEvent(&events.LoggedOut{Reason: events.ConnectFailureLoggedOut})
		close(dispatched)
	}()
	<-repo.entered
	cancel() // The lifecycle worker exits before the in-flight DB operation returns.
	retired := make(chan struct{})
	go func() { client.RemoveEventHandlers(); close(retired) }()
	close(repo.release)
	select {
	case <-retired:
	case <-time.After(time.Second):
		// Release the old blocking send so the red test does not leak goroutines.
		select {
		case <-kill:
		case <-time.After(time.Second):
		}
		<-dispatched
		<-retired
		t.Fatal("canceled logout handler blocked event-handler removal")
	}
	<-dispatched
}

func TestStartInstancePreservesActiveWorkerChannel(t *testing.T) {
	readyForReconnectTest(t)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	kill := make(chan bool)
	cfg := &config.Config{LogDirectory: t.TempDir()}
	w := &whatsmeowService{
		config: cfg, loggerWrapper: logger_wrapper.NewLoggerManager(cfg),
		userInfoCache:   cache.New(time.Minute, time.Minute),
		killChannel:     map[string]chan bool{"test": kill},
		myClientPointer: map[string]*MyClient{"test": {ctx: ctx, killSignal: kill}},
		instanceRepository: &reconnectTestRepository{get: func(string) (*instance_model.Instance, error) {
			// Invalid proxy prevents the old code from launching any real client.
			return &instance_model.Instance{Id: "test", Proxy: "{"}, nil
		}},
	}
	_ = w.StartInstance("test")
	if w.killChannel["test"] != kill {
		t.Fatal("redundant start replaced the active worker's published stop channel")
	}
}

func TestClearCacheCancelsCallbacksWithoutClosingTheirSignal(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	kill := make(chan bool)
	mycli := &MyClient{ctx: ctx, cancel: cancel, killSignal: kill, userID: "test"}
	cfg := &config.Config{LogDirectory: t.TempDir()}
	w := &whatsmeowService{
		myClientPointer: map[string]*MyClient{"test": mycli},
		killChannel:     map[string]chan bool{"test": kill},
		userInfoCache:   cache.New(time.Minute, time.Minute),
		loggerWrapper:   logger_wrapper.NewLoggerManager(cfg),
	}
	if err := w.ClearInstanceCache("test", ""); err != nil {
		t.Fatal(err)
	}
	defer func() {
		if err := recover(); err != nil {
			t.Fatalf("late callback panicked after cache deletion: %v", err)
		}
	}()
	mycli.signalStop()
	if ctx.Err() == nil {
		t.Fatal("deleted generation's callbacks were not canceled")
	}
}

func TestReconnectRetiresWorkerStillInitializingStore(t *testing.T) {
	readyForReconnectTest(t)
	ctx, cancel := context.WithCancel(context.Background())
	stopped := make(chan struct{})
	run := &clientRun{ctx: ctx, cancel: cancel, stopped: stopped}
	go func() { <-ctx.Done(); close(stopped) }()
	t.Cleanup(func() { cancel(); <-stopped })
	errStop := errors.New("stop before replacement")
	cfg := &config.Config{LogDirectory: t.TempDir()}
	w := &whatsmeowService{loggerWrapper: logger_wrapper.NewLoggerManager(cfg),
		instanceRepository: &reconnectTestRepository{get: func(string) (*instance_model.Instance, error) {
			select {
			case <-stopped:
			default:
				t.Error("replacement bookkeeping began while old store initialization could still publish a client")
			}
			return nil, errStop
		}}}
	w.starts.Store("test", run)
	_ = w.ReconnectClient("test")
}

func TestStartClientWaitsForRetiringReservation(t *testing.T) {
	resetWAVersionInitializationForTest()
	t.Cleanup(resetWAVersionInitializationForTest)
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	old := &clientRun{ctx: ctx, cancel: cancel, stopped: make(chan struct{})}
	cfg := &config.Config{LogDirectory: t.TempDir()}
	w := &whatsmeowService{config: cfg, loggerWrapper: logger_wrapper.NewLoggerManager(cfg)}
	w.starts.Store("test", old)
	returned := make(chan struct{})
	go func() { w.StartClient(&ClientData{Instance: &instance_model.Instance{Id: "test"}}); close(returned) }()
	select {
	case <-returned:
		t.Error("replacement was silently discarded while the old generation was retiring")
	case <-time.After(100 * time.Millisecond):
	}
	w.starts.Delete("test")
	close(old.stopped)
	select {
	case <-returned:
	case <-time.After(time.Second):
		t.Fatal("replacement did not proceed after retirement")
	}
	// The new worker exits at the readiness gate, before store/network work.
	if value, exists := w.starts.Load("test"); exists {
		<-value.(*clientRun).stopped
	}
}

type disconnectedRecordingRepository struct {
	instance_repository.InstanceRepository
	writes atomic.Int32
}

func (r *disconnectedRecordingRepository) UpdateConnected(string, bool, string) error {
	r.writes.Add(1)
	return nil
}

func TestCanceledDisconnectCannotOverwriteReplacementStatus(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	cfg := &config.Config{LogDirectory: t.TempDir()}
	repo := &disconnectedRecordingRepository{}
	client := &MyClient{ctx: ctx, userID: "test", Instance: &instance_model.Instance{Id: "test"},
		instanceRepository: repo, userInfoCache: cache.New(time.Minute, time.Minute), config: cfg,
		loggerWrapper: logger_wrapper.NewLoggerManager(cfg),
		service:       &disconnectedCaptureService{archiveCaptureService: archiveCaptureService{calls: make(chan archiveWebhookCall, 1)}},
	}
	client.myEventHandler(&events.Disconnected{})
	if repo.writes.Load() != 0 {
		t.Fatal("canceled generation overwrote the replacement's connection status")
	}
}

type disconnectedCaptureService struct{ archiveCaptureService }

func (*disconnectedCaptureService) ReconnectClient(string) error { return nil }

func TestReconnectDoesNotLoseNewGenerationJoiningOlderJob(t *testing.T) {
	readyForReconnectTest(t)
	old := whatsmeow.NewClient(&store.Device{}, nil)
	replacement := whatsmeow.NewClient(&store.Device{}, nil)
	entered, release := make(chan struct{}), make(chan struct{})
	var calls atomic.Int32
	stop := errors.New("controlled store stop")
	cfg := &config.Config{LogDirectory: t.TempDir()}
	w := &whatsmeowService{clientPointer: map[string]*whatsmeow.Client{"test": old},
		loggerWrapper: logger_wrapper.NewLoggerManager(cfg),
		instanceRepository: &reconnectTestRepository{get: func(string) (*instance_model.Instance, error) {
			if calls.Add(1) == 1 {
				close(entered)
				<-release
			}
			return nil, stop
		}}}
	results := make(chan error, 2)
	go func() { results <- w.reconnectClient("test", old) }()
	<-entered
	// Another connect publishes a new generation during the first job's I/O.
	w.clientPointer["test"] = replacement
	joining := make(chan struct{})
	go func() { close(joining); results <- w.reconnectClient("test", replacement) }()
	<-joining
	time.Sleep(100 * time.Millisecond)
	close(release)
	for range 2 {
		select {
		case <-results:
		case <-time.After(2 * time.Second):
			t.Fatal("reconnect did not finish")
		}
	}
	if !replacement.DangerousInternals().IsExpectedDisconnect() {
		t.Fatal("new generation's recovery joined the old job and was silently lost")
	}
}

func TestRuntimeSettingsRejectRetiringGeneration(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	cfg := &config.Config{LogDirectory: t.TempDir()}
	w := &whatsmeowService{loggerWrapper: logger_wrapper.NewLoggerManager(cfg),
		userInfoCache:   cache.New(time.Minute, time.Minute),
		myClientPointer: map[string]*MyClient{"test": {ctx: ctx, WAClient: whatsmeow.NewClient(&store.Device{}, nil)}},
		instanceRepository: &reconnectTestRepository{get: func(string) (*instance_model.Instance, error) {
			return &instance_model.Instance{Id: "test"}, nil
		}}}
	if err := w.UpdateInstanceSettings("test"); err == nil {
		t.Fatal("connect fast path accepted a worker that is already retiring")
	}
}

func TestStartCannotOvertakeCompleteRetirement(t *testing.T) {
	readyForReconnectTest(t)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	run := &clientRun{ctx: ctx, cancel: cancel, stopped: make(chan struct{})}
	client := whatsmeow.NewClient(&store.Device{}, nil)
	handlerEntered, release := make(chan struct{}), make(chan struct{})
	var once sync.Once
	unblock := func() { once.Do(func() { close(release) }) }
	t.Cleanup(unblock)
	client.AddEventHandler(func(any) { close(handlerEntered); <-release })
	dispatched := make(chan struct{})
	go func() { client.DangerousInternals().DispatchEvent(&events.Archive{}); close(dispatched) }()
	<-handlerEntered
	getCalled := make(chan struct{}, 1)
	cfg := &config.Config{LogDirectory: t.TempDir()}
	w := &whatsmeowService{clientPointer: map[string]*whatsmeow.Client{"test": client},
		loggerWrapper: logger_wrapper.NewLoggerManager(cfg), userInfoCache: cache.New(time.Minute, time.Minute),
		instanceRepository: &reconnectTestRepository{get: func(string) (*instance_model.Instance, error) {
			getCalled <- struct{}{}
			return nil, errors.New("stop before network")
		}}}
	w.starts.Store("test", run)
	go func() { <-ctx.Done(); w.starts.Delete("test"); close(run.stopped) }()
	retired := make(chan struct{})
	go func() { _ = w.ClearInstanceCache("test", ""); close(retired) }()
	deadline := time.Now().Add(time.Second)
	for !client.DangerousInternals().IsExpectedDisconnect() && time.Now().Before(deadline) {
		time.Sleep(time.Millisecond)
	}
	if !client.DangerousInternals().IsExpectedDisconnect() {
		t.Fatal("retirement did not reach handler-drain barrier")
	}
	started := make(chan struct{})
	go func() { _ = w.StartInstance("test"); close(started) }()
	select {
	case <-getCalled:
		t.Error("new start entered while old generation cleanup still owned published pointers")
	case <-time.After(100 * time.Millisecond):
	}
	unblock()
	<-dispatched
	<-retired
	<-started
}

func TestRepeatedStartPreservesLatestPendingSettings(t *testing.T) {
	for _, published := range []bool{false, true} {
		t.Run(fmt.Sprint("published_", published), func(t *testing.T) {
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			original := &ClientData{Instance: &instance_model.Instance{Id: "test", Webhook: "http://old.invalid"}}
			latest := &ClientData{Instance: &instance_model.Instance{Id: "test", Webhook: "http://new.invalid"}, Subscriptions: []string{"Archive"}}
			run := &clientRun{ctx: ctx, cancel: cancel, stopped: make(chan struct{}), data: original}
			w := &whatsmeowService{myClientPointer: make(map[string]*MyClient), userInfoCache: cache.New(time.Minute, time.Minute)}
			if published {
				w.myClientPointer["test"] = &MyClient{ctx: ctx, Instance: original.Instance}
			}
			w.starts.Store("test", run)
			w.StartClient(latest)
			if run.data.Instance.Webhook != latest.Instance.Webhook || len(run.data.Subscriptions) != 1 {
				t.Fatal("successful repeated start discarded the pending webhook/subscription update")
			}
			if published && w.myClientPointer["test"].webhookUrl != latest.Instance.Webhook {
				t.Fatal("update arrived during publication but active worker kept stale webhook")
			}
		})
	}
}
