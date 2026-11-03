package whatsmeow_service

import (
	"fmt"
	"io"
	"net/http"
	"regexp"
	"strconv"
	"time"

	"github.com/evolution-foundation/evolution-go/pkg/config"
	"github.com/gomessguii/logger"
	"go.mau.fi/whatsmeow/proto/waCompanionReg"
	"go.mau.fi/whatsmeow/proto/waWa6"
	"go.mau.fi/whatsmeow/store"
	"google.golang.org/protobuf/proto"
)

var revisionPattern = regexp.MustCompile(`(?:["']client_revision["']|\\"client_revision\\"|client_revision)\s*:\s*(\d+)`)

// InitializeWAVersion must run once, before any whatsmeow clients or goroutines.
// The library's version, registration hash and payload are process-wide globals.
func InitializeWAVersion(cfg *config.Config) error {
	version, err := selectWAVersion(cfg, fetchWhatsAppWebVersion)
	if err != nil {
		version = store.GetWAVersion()
	}
	store.SetWAVersion(version)
	store.DeviceProps.PlatformType = waCompanionReg.DeviceProps_CHROME.Enum()
	store.DeviceProps.RequireFullSync = proto.Bool(true)
	store.DeviceProps.Version.Primary = proto.Uint32(version[0])
	store.DeviceProps.Version.Secondary = proto.Uint32(version[1])
	store.DeviceProps.Version.Tertiary = proto.Uint32(version[2])
	logger.LogInfo("WhatsApp handshake version: %s (fixed until process restart)", version.String())
	return err
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
