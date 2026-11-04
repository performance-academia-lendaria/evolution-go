package whatsmeow_service

import (
	"bytes"
	"errors"
	"io"
	"net/http"
	"strings"
	"sync"
	"sync/atomic"
	"testing"

	"github.com/evolution-foundation/evolution-go/pkg/config"
	"go.mau.fi/whatsmeow/proto/waCompanionReg"
	"go.mau.fi/whatsmeow/store"
	"go.mau.fi/whatsmeow/types"
	"go.mau.fi/whatsmeow/util/keys"
	"google.golang.org/protobuf/proto"
)

func TestSelectWAVersion(t *testing.T) {
	web := store.WAVersionContainer{2, 3000, 1052878631}
	failure := errors.New("offline")
	for _, tc := range []struct {
		name     string
		cfg      config.Config
		fetchErr error
		want     store.WAVersionContainer
		wantErr  bool
		calls    int
	}{
		{"web", config.Config{}, nil, web, false, 1},
		{"manual overrides web", config.Config{WhatsappVersionMajor: 2, WhatsappVersionMinor: 3000, WhatsappVersionPatch: 42}, failure, store.WAVersionContainer{2, 3000, 42}, false, 0},
		{"partial", config.Config{WhatsappVersionMajor: 2}, nil, store.WAVersionContainer{}, true, 0},
		{"negative", config.Config{WhatsappVersionMajor: -1, WhatsappVersionMinor: 3000, WhatsappVersionPatch: 42}, nil, store.WAVersionContainer{}, true, 0},
		{"offline", config.Config{}, failure, store.WAVersionContainer{}, true, 1},
	} {
		t.Run(tc.name, func(t *testing.T) {
			calls := 0
			got, err := selectWAVersion(&tc.cfg, func() (store.WAVersionContainer, error) {
				calls++
				if tc.fetchErr != nil {
					return store.WAVersionContainer{}, tc.fetchErr
				}
				return web, nil
			})
			if got != tc.want || (err != nil) != tc.wantErr || calls != tc.calls {
				t.Fatalf("got %v, err %v, calls %d", got, err, calls)
			}
		})
	}
}

func TestHandshakeVersionAndConcurrentDeviceNames(t *testing.T) {
	oldVersion := store.GetWAVersion()
	oldProps := proto.Clone(store.DeviceProps).(*waCompanionReg.DeviceProps)
	resetWAVersionInitializationForTest()
	t.Cleanup(func() {
		store.SetWAVersion(oldVersion)
		store.DeviceProps = oldProps
		resetWAVersionInitializationForTest()
	})
	version := store.WAVersionContainer{2, 3000, 1052878631}
	if err := InitializeWAVersion(&config.Config{WhatsappVersionMajor: int(version[0]), WhatsappVersionMinor: int(version[1]), WhatsappVersionPatch: int(version[2])}); err != nil {
		t.Fatal(err)
	}
	identity := keys.NewKeyPair()
	device := &store.Device{IdentityKey: identity, SignedPreKey: identity.CreateSignedPreKey(1)}
	payload := device.GetClientPayload()
	app := payload.GetUserAgent().GetAppVersion()
	if app.GetPrimary() != version[0] || app.GetSecondary() != version[1] || app.GetTertiary() != version[2] {
		t.Fatalf("incorrect registration version: %v", app)
	}
	hash := version.Hash()
	if !bytes.Equal(payload.GetDevicePairingData().GetBuildHash(), hash[:]) {
		t.Fatal("registration hash does not match handshake version")
	}
	jid := types.NewJID("123456789", types.DefaultUserServer)
	login := (&store.Device{ID: &jid}).GetClientPayload().GetUserAgent().GetAppVersion()
	if login.GetPrimary() != version[0] || login.GetSecondary() != version[1] || login.GetTertiary() != version[2] {
		t.Fatalf("incorrect login version: %v", login)
	}
	var wg sync.WaitGroup
	for _, name := range []string{"first", "second"} {
		wg.Add(1)
		go func(name string) {
			defer wg.Done()
			for i := 0; i < 100; i++ {
				p := payloadWithDeviceOS(device.GetClientPayload(), name)
				props := &waCompanionReg.DeviceProps{}
				if err := proto.Unmarshal(p.GetDevicePairingData().GetDeviceProps(), props); err != nil {
					t.Error(err)
					return
				}
				if props.GetOs() != name || props.GetVersion().GetTertiary() != version[2] {
					t.Errorf("wrong device props: %v", props)
					return
				}
			}
		}(name)
	}
	wg.Wait()
}

func TestRevisionPattern(t *testing.T) {
	for _, value := range []string{`{"client_revision":1052878631}`, `{\"client_revision\": 1052878631}`, `{'client_revision': 1052878631}`, `{client_revision:1052878631}`} {
		match := revisionPattern.FindStringSubmatch(value)
		if len(match) != 2 || match[1] != "1052878631" {
			t.Fatalf("no revision in %q", value)
		}
	}
}

type roundTripperFunc func(*http.Request) (*http.Response, error)

func (fn roundTripperFunc) RoundTrip(req *http.Request) (*http.Response, error) { return fn(req) }

func TestVersionInitializationRetriesAfterLookupFailure(t *testing.T) {
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
	store.DeviceProps.PlatformType = waCompanionReg.DeviceProps_UNKNOWN.Enum()
	before := proto.Clone(store.DeviceProps).(*waCompanionReg.DeviceProps)
	var calls atomic.Int32
	http.DefaultTransport = roundTripperFunc(func(*http.Request) (*http.Response, error) {
		if calls.Add(1) == 1 {
			return nil, errors.New("temporary failure")
		}
		return &http.Response{StatusCode: http.StatusOK, Body: io.NopCloser(strings.NewReader(`{"client_revision":1052878631}`)), Header: make(http.Header)}, nil
	})
	if err := InitializeWAVersion(&config.Config{}); err == nil {
		t.Fatal("expected lookup failure")
	}
	if !proto.Equal(before, store.DeviceProps) || store.GetWAVersion() != oldVersion {
		t.Fatal("failed initialization modified whatsmeow state")
	}
	var wg sync.WaitGroup
	for i := 0; i < 16; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			if err := InitializeWAVersion(&config.Config{}); err != nil {
				t.Errorf("retry failed: %v", err)
			}
		}()
	}
	wg.Wait()
	want := store.WAVersionContainer{2, 3000, 1052878631}
	if store.GetWAVersion() != want {
		t.Fatalf("retry did not apply fetched version")
	}
	if err := InitializeWAVersion(&config.Config{}); err != nil {
		t.Fatal(err)
	}
	if calls.Load() != 2 {
		t.Fatalf("expected version to be frozen after success, got %d lookups", calls.Load())
	}
}

// Tests are sequential and wait for all client goroutines before resetting globals.
func resetWAVersionInitializationForTest() {
	waVersionInitialization.initialized = false
	waVersionInitialization.ready = make(chan struct{})
}

func TestMalformedManualVersionDoesNotFallBackToWeb(t *testing.T) {
	t.Setenv("POSTGRES_USERS_DB", "postgres://test:test@localhost/test")
	t.Setenv("DATABASE_SAVE_MESSAGES", "false")
	t.Setenv("GLOBAL_API_KEY", "test-key")
	t.Setenv("MINIO_ENABLED", "false")
	t.Setenv("AMQP_URL", "")
	for _, tc := range []struct {
		name, major, minor, patch string
	}{
		{"non-numeric", "abc", "def", "ghi"},
		{"overflow", "18446744073709551616", "18446744073709551616", "18446744073709551616"},
		{"zeros", "0", "0", "0"},
		{"partial", "2", "3000", ""},
		{"negative", "2", "3000", "-1"},
		{"outside-uint32", "2", "3000", "4294967296"},
	} {
		t.Run(tc.name, func(t *testing.T) {
			t.Setenv("WHATSAPP_VERSION_MAJOR", tc.major)
			t.Setenv("WHATSAPP_VERSION_MINOR", tc.minor)
			t.Setenv("WHATSAPP_VERSION_PATCH", tc.patch)
			cfg := config.Load()
			called := false
			_, err := selectWAVersion(cfg, func() (store.WAVersionContainer, error) {
				called = true
				return store.WAVersionContainer{2, 3000, 1052878631}, nil
			})
			if err == nil || called {
				t.Fatalf("invalid manual settings must fail without fetching a web version")
			}
		})
	}
}

func TestManualAndAutomaticVersionsFromEnvironment(t *testing.T) {
	t.Setenv("POSTGRES_USERS_DB", "postgres://test:test@localhost/test")
	t.Setenv("DATABASE_SAVE_MESSAGES", "false")
	t.Setenv("GLOBAL_API_KEY", "test-key")
	t.Setenv("MINIO_ENABLED", "false")
	t.Setenv("AMQP_URL", "")
	for _, tc := range []struct {
		name, major, minor, patch string
		wantFetch                 bool
	}{
		{"manual", "2", "3000", "1052878631", false},
		{"automatic", "", "", "", true},
	} {
		t.Run(tc.name, func(t *testing.T) {
			t.Setenv("WHATSAPP_VERSION_MAJOR", tc.major)
			t.Setenv("WHATSAPP_VERSION_MINOR", tc.minor)
			t.Setenv("WHATSAPP_VERSION_PATCH", tc.patch)
			called := false
			want := store.WAVersionContainer{2, 3000, 1052878631}
			got, err := selectWAVersion(config.Load(), func() (store.WAVersionContainer, error) { called = true; return want, nil })
			if err != nil || got != want || called != tc.wantFetch {
				t.Fatalf("unexpected version selection: got %v, err %v, fetched %v", got, err, called)
			}
		})
	}
}
