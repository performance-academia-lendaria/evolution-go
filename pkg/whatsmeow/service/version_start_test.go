package whatsmeow_service

import (
	"context"
	"errors"
	"io"
	"net/http"
	"strings"
	"sync/atomic"
	"testing"
	"time"

	"github.com/evolution-foundation/evolution-go/pkg/config"
	instance_model "github.com/evolution-foundation/evolution-go/pkg/instance/model"
	instance_repository "github.com/evolution-foundation/evolution-go/pkg/instance/repository"
	logger_wrapper "github.com/evolution-foundation/evolution-go/pkg/logger"
	"go.mau.fi/whatsmeow/proto/waCompanionReg"
	"go.mau.fi/whatsmeow/store"
	"google.golang.org/protobuf/proto"
)

type versionGateRepository struct {
	instance_repository.InstanceRepository
	startupCalled chan struct{}
	getCalled     bool
}

func (r *versionGateRepository) GetInstanceByID(string) (*instance_model.Instance, error) {
	r.getCalled = true
	return nil, errors.New("repository should not be reached")
}

func (r *versionGateRepository) GetAllConnectedInstances() ([]*instance_model.Instance, error) {
	r.startupCalled <- struct{}{}
	return nil, nil
}

func TestStartInstanceRejectsWhileVersionUnavailable(t *testing.T) {
	resetWAVersionInitializationForTest()
	repo := &versionGateRepository{}
	w := whatsmeowService{instanceRepository: repo}
	err := w.StartInstance("test")
	if err == nil || repo.getCalled {
		t.Fatalf("client start should fail before reaching the repository while version is unavailable: %v", err)
	}
}

func TestStartupWaitsForVersionBeforeLoadingInstances(t *testing.T) {
	oldVersion := store.GetWAVersion()
	oldProps := proto.Clone(store.DeviceProps).(*waCompanionReg.DeviceProps)
	resetWAVersionInitializationForTest()
	t.Cleanup(func() {
		store.SetWAVersion(oldVersion)
		store.DeviceProps = oldProps
		resetWAVersionInitializationForTest()
	})
	repo := &versionGateRepository{startupCalled: make(chan struct{}, 1)}
	cfg := &config.Config{LogDirectory: t.TempDir()}
	w := whatsmeowService{instanceRepository: repo, loggerWrapper: logger_wrapper.NewLoggerManager(cfg)}
	done := make(chan struct{})
	go func() { w.ConnectOnStartup(""); close(done) }()
	t.Cleanup(func() {
		select {
		case <-done:
		case <-time.After(2 * time.Second):
			t.Error("startup did not stop")
		}
	})
	select {
	case <-repo.startupCalled:
		t.Fatal("startup loaded instances before version initialization")
	case <-time.After(100 * time.Millisecond):
	}
	if err := InitializeWAVersion(&config.Config{WhatsappVersionMajor: 2, WhatsappVersionMinor: 3000, WhatsappVersionPatch: 1052878631}); err != nil {
		t.Fatal(err)
	}
	select {
	case <-repo.startupCalled:
	case <-time.After(2 * time.Second):
		t.Fatal("startup did not resume after version initialization")
	}
}

func TestBackgroundVersionRetryRecovers(t *testing.T) {
	oldVersion := store.GetWAVersion()
	oldProps := proto.Clone(store.DeviceProps).(*waCompanionReg.DeviceProps)
	oldTransport := http.DefaultTransport
	resetWAVersionInitializationForTest()
	t.Cleanup(func() {
		store.SetWAVersion(oldVersion)
		store.DeviceProps = oldProps
		http.DefaultTransport = oldTransport
		resetWAVersionInitializationForTest()
	})
	var calls atomic.Int32
	http.DefaultTransport = roundTripperFunc(func(*http.Request) (*http.Response, error) {
		if calls.Add(1) == 1 {
			return nil, errors.New("temporarily offline")
		}
		return &http.Response{StatusCode: http.StatusOK, Body: io.NopCloser(strings.NewReader(`{"client_revision":1052878631}`)), Header: make(http.Header)}, nil
	})
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	done := make(chan struct{})
	go func() { retryWAVersionInitialization(ctx, &config.Config{}, time.Millisecond); close(done) }()
	select {
	case <-waVersionInitialization.ready:
	case <-ctx.Done():
		t.Fatal("background retry never initialized the version")
	}
	<-done
	if calls.Load() != 2 || store.GetWAVersion() != (store.WAVersionContainer{2, 3000, 1052878631}) {
		t.Fatalf("retry did not recover using the fetched version; calls=%d", calls.Load())
	}
}
