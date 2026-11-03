package whatsmeow_service

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"regexp"
	"strconv"
	"sync"
	"time"

	"github.com/evolution-foundation/evolution-go/pkg/config"
	"github.com/evolution-foundation/evolution-go/pkg/utils"
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
func RetryWAVersionInitialization(ctx context.Context, cfg *config.Config, loadProxies func(context.Context) ([]string, error)) {
	retryWAVersionInitialization(ctx, cfg, loadProxies, 10*time.Second)
}

func retryWAVersionInitialization(ctx context.Context, cfg *config.Config, loadProxies func(context.Context) ([]string, error), interval time.Duration) {
	for {
		if ctx.Err() != nil {
			return
		}
		if err := initializeWAVersion(ctx, cfg, loadProxies); err == nil {
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
	return initializeWAVersion(context.Background(), cfg, nil)
}

func initializeWAVersion(ctx context.Context, cfg *config.Config, loadProxies func(context.Context) ([]string, error)) error {
	waVersionInitialization.mu.Lock()
	defer waVersionInitialization.mu.Unlock()
	if waVersionInitialization.initialized {
		return nil
	}
	version, err := selectWAVersion(cfg, func() (store.WAVersionContainer, error) {
		return fetchWhatsAppWebVersion(ctx, cfg, loadProxies)
	})
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

// fetchWhatsAppWebVersion first respects normal HTTP proxy settings, then tries
// the application's global and saved per-instance proxies. Proxy credentials
// never appear in returned errors or logs.
func fetchWhatsAppWebVersion(ctx context.Context, cfg *config.Config, loadProxies func(context.Context) ([]string, error)) (store.WAVersionContainer, error) {
	if version, err := fetchVersionWithClient(ctx, &http.Client{Timeout: 10 * time.Second}); err == nil {
		return version, nil
	}
	seen := make(map[string]bool)
	tryProxies := func(addresses []string) (store.WAVersionContainer, bool) {
		for _, address := range addresses {
			if seen[address] {
				continue
			}
			seen[address] = true
			proxyURL, err := url.Parse(address)
			if err != nil {
				continue
			}
			transport := &http.Transport{}
			if base, ok := http.DefaultTransport.(*http.Transport); ok {
				transport = base.Clone()
			}
			transport.Proxy = http.ProxyURL(proxyURL)
			client := &http.Client{Timeout: 10 * time.Second, Transport: transport}
			version, err := fetchVersionWithClient(ctx, client)
			transport.CloseIdleConnections()
			if err == nil {
				return version, true
			}
			if ctx.Err() != nil {
				break
			}
		}
		return store.WAVersionContainer{}, false
	}
	if version, ok := tryProxies(whatsappVersionProxyAddresses(cfg, nil)); ok {
		return version, nil
	}
	if loadProxies != nil && ctx.Err() == nil {
		lookupCtx, cancel := context.WithTimeout(ctx, 3*time.Second)
		proxies, err := loadProxies(lookupCtx)
		cancel()
		if err != nil {
			logger.LogWarn("Could not load instance proxies for WhatsApp version lookup")
		} else if version, ok := tryProxies(whatsappVersionProxyAddresses(cfg, proxies)); ok {
			return version, nil
		}
	}
	return store.WAVersionContainer{}, fmt.Errorf("WhatsApp Web version unavailable through direct access or configured proxies")
}

func whatsappVersionProxyAddresses(cfg *config.Config, rawProxies []string) []string {
	global := ProxyConfig{Protocol: cfg.ProxyProtocol, Host: cfg.ProxyHost, Port: cfg.ProxyPort, Username: cfg.ProxyUsername, Password: cfg.ProxyPassword}
	candidates := []ProxyConfig{global}
	for _, raw := range rawProxies {
		var p ProxyConfig
		if json.Unmarshal([]byte(raw), &p) != nil {
			continue
		}
		if p.Host == "" {
			p.Host = global.Host
		}
		if p.Port == "" {
			p.Port = global.Port
		}
		if p.Protocol == "" {
			p.Protocol = global.Protocol
		}
		if p.Username == "" {
			p.Username = global.Username
		}
		if p.Password == "" {
			p.Password = global.Password
		}
		candidates = append(candidates, p)
	}
	seen := make(map[string]bool)
	var addresses []string
	for _, p := range candidates {
		address, err := utils.BuildProxyAddress(p.Protocol, p.Host, p.Port, p.Username, p.Password)
		if err == nil && !seen[address] {
			seen[address] = true
			addresses = append(addresses, address)
		}
	}
	return addresses
}

func fetchVersionWithClient(ctx context.Context, client *http.Client) (store.WAVersionContainer, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, "https://web.whatsapp.com/sw.js", nil)
	if err != nil {
		return store.WAVersionContainer{}, err
	}
	resp, err := client.Do(req)
	if err != nil {
		return store.WAVersionContainer{}, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return store.WAVersionContainer{}, fmt.Errorf("unexpected HTTP status")
	}
	body, err := io.ReadAll(io.LimitReader(resp.Body, 10<<20))
	if err != nil {
		return store.WAVersionContainer{}, err
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
