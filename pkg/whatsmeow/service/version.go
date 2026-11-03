package whatsmeow_service

import (
	"context"
	"errors"
	"fmt"
	"io"
	"net/http"
	"regexp"
	"strconv"
	"sync"
	"time"

	"github.com/evolution-foundation/evolution-go/pkg/config"
	"github.com/gomessguii/logger"
	"go.mau.fi/whatsmeow/proto/waCompanionReg"
	"go.mau.fi/whatsmeow/proto/waWa6"
	"go.mau.fi/whatsmeow/store"
	"google.golang.org/protobuf/proto"
)

var revisionPattern = regexp.MustCompile(`(?:["']client_revision["']|\\"client_revision\\"|client_revision)\s*:\s*(\d+)`)

// waVersionInitialization protects initialization until the first successful
// lookup. No client may start until it succeeds; afterwards globals are immutable.
var waVersionInitialization = struct {
	mu          sync.Mutex
	initialized bool
	ready       chan struct{}
}{ready: make(chan struct{})}

// ErrWAVersionNotReady indicates that clients cannot safely start yet.
var ErrWAVersionNotReady = errors.New("WhatsApp version is not ready; retry shortly")

// WAVersionReady reports readiness without waiting for an in-flight lookup.
func WAVersionReady() bool {
	select {
	case <-waVersionInitialization.ready:
		return true
	default:
		return false
	}
}

// RetryWAVersionInitialization retries in the background until successful or cancelled.
func RetryWAVersionInitialization(ctx context.Context, cfg *config.Config) {
	retryWAVersionInitialization(ctx, cfg, 10*time.Second)
}

func retryWAVersionInitialization(ctx context.Context, cfg *config.Config, interval time.Duration) {
	for {
		if ctx.Err() != nil {
			return
		}
		if err := InitializeWAVersion(cfg); err == nil {
			return
		} else {
			logger.LogWarn("WhatsApp version unavailable; retrying: %v", err)
		}
		timer := time.NewTimer(interval)
		select {
		case <-ctx.Done():
			timer.Stop()
			return
		case <-timer.C:
		}
	}
}

// InitializeWAVersion retries failed lookups but never changes the shared
// whatsmeow state after the first successful initialization.
func InitializeWAVersion(cfg *config.Config) error {
	waVersionInitialization.mu.Lock()
	defer waVersionInitialization.mu.Unlock()
	if waVersionInitialization.initialized {
		return nil
	}
	version, err := selectWAVersion(cfg, fetchWhatsAppWebVersion)
	if err != nil {
		return err
	}
	store.SetWAVersion(version)
	store.DeviceProps.PlatformType = waCompanionReg.DeviceProps_CHROME.Enum()
	store.DeviceProps.RequireFullSync = proto.Bool(true)
	store.DeviceProps.Version.Primary = proto.Uint32(version[0])
	store.DeviceProps.Version.Secondary = proto.Uint32(version[1])
	store.DeviceProps.Version.Tertiary = proto.Uint32(version[2])
	waVersionInitialization.initialized = true
	close(waVersionInitialization.ready)
	logger.LogInfo("WhatsApp handshake version: %s (fixed until process restart)", version.String())
	return nil
}

func selectWAVersion(cfg *config.Config, fetch func() (store.WAVersionContainer, error)) (store.WAVersionContainer, error) {
	parts := [3]int{cfg.WhatsappVersionMajor, cfg.WhatsappVersionMinor, cfg.WhatsappVersionPatch}
	if parts != [3]int{} {
		for _, part := range parts {
			if part <= 0 || uint64(part) > uint64(^uint32(0)) {
				return store.WAVersionContainer{}, fmt.Errorf("WHATSAPP_VERSION requires three positive uint32 components")
			}
		}
		return store.WAVersionContainer{uint32(parts[0]), uint32(parts[1]), uint32(parts[2])}, nil
	}
	return fetch()
}

func fetchWhatsAppWebVersion() (store.WAVersionContainer, error) {
	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Get("https://web.whatsapp.com/sw.js")
	if err != nil {
		return store.WAVersionContainer{}, fmt.Errorf("fetch WhatsApp Web version: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return store.WAVersionContainer{}, fmt.Errorf("fetch WhatsApp Web version: HTTP %d", resp.StatusCode)
	}
	body, err := io.ReadAll(io.LimitReader(resp.Body, 10<<20))
	if err != nil {
		return store.WAVersionContainer{}, fmt.Errorf("read WhatsApp Web version: %w", err)
	}
	matches := revisionPattern.FindSubmatch(body)
	if len(matches) != 2 {
		return store.WAVersionContainer{}, fmt.Errorf("WhatsApp Web client revision not found")
	}
	revision, err := strconv.ParseUint(string(matches[1]), 10, 32)
	if err != nil || revision == 0 {
		return store.WAVersionContainer{}, fmt.Errorf("invalid WhatsApp Web client revision")
	}
	return store.WAVersionContainer{2, 3000, uint32(revision)}, nil
}

func payloadWithDeviceOS(payload *waWa6.ClientPayload, name string) *waWa6.ClientPayload {
	registration := payload.GetDevicePairingData()
	if registration == nil {
		return payload
	}
	props := &waCompanionReg.DeviceProps{}
	if err := proto.Unmarshal(registration.GetDeviceProps(), props); err != nil {
		return payload
	}
	props.Os = proto.String(name)
	if encoded, err := proto.Marshal(props); err == nil {
		registration.DeviceProps = encoded
	}
	return payload
}
