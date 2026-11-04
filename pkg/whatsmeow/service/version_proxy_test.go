package whatsmeow_service

import (
	"bufio"
	"context"
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/base64"
	"encoding/json"
	"encoding/pem"
	"errors"
	"fmt"
	"math/big"
	"net"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/evolution-foundation/evolution-go/pkg/config"
	"go.mau.fi/whatsmeow/proto/waCompanionReg"
	"go.mau.fi/whatsmeow/store"
	"google.golang.org/protobuf/proto"
)

// testVersionProxy is an actual HTTP CONNECT proxy with a local TLS endpoint.
// Direct network access is disabled; no request leaves the test host.
func testVersionProxy(t *testing.T, expectedAuth string) (string, string, *http.Transport) {
	t.Helper()
	key, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	tmpl := &x509.Certificate{SerialNumber: big.NewInt(1), Subject: pkix.Name{CommonName: "web.whatsapp.com"}, DNSNames: []string{"web.whatsapp.com"}, NotBefore: time.Now().Add(-time.Hour), NotAfter: time.Now().Add(time.Hour), KeyUsage: x509.KeyUsageDigitalSignature | x509.KeyUsageCertSign, ExtKeyUsage: []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth}, BasicConstraintsValid: true, IsCA: true}
	der, err := x509.CreateCertificate(rand.Reader, tmpl, tmpl, key.Public(), key)
	if err != nil {
		t.Fatal(err)
	}
	keyDER, err := x509.MarshalPKCS8PrivateKey(key)
	if err != nil {
		t.Fatal(err)
	}
	cert, err := tls.X509KeyPair(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der}), pem.EncodeToMemory(&pem.Block{Type: "PRIVATE KEY", Bytes: keyDER}))
	if err != nil {
		t.Fatal(err)
	}
	ca := x509.NewCertPool()
	if !ca.AppendCertsFromPEM(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der})) {
		t.Fatal("failed to add test CA")
	}
	proxy := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if got := r.Header.Get("Proxy-Authorization"); got != expectedAuth {
			t.Errorf("incorrect proxy authentication")
			http.Error(w, "proxy auth", http.StatusProxyAuthRequired)
			return
		}
		if r.Method != http.MethodConnect || r.Host != "web.whatsapp.com:443" {
			t.Errorf("unexpected proxy request")
			http.Error(w, "bad request", 400)
			return
		}
		conn, rw, err := w.(http.Hijacker).Hijack()
		if err != nil {
			t.Error(err)
			return
		}
		defer conn.Close()
		if _, err := rw.WriteString("HTTP/1.1 200 Connection Established\r\n\r\n"); err != nil {
			t.Error(err)
			return
		}
		if err := rw.Flush(); err != nil {
			t.Error(err)
			return
		}
		tlsConn := tls.Server(conn, &tls.Config{Certificates: []tls.Certificate{cert}, MinVersion: tls.VersionTLS12})
		if _, err := http.ReadRequest(bufio.NewReader(tlsConn)); err != nil {
			t.Error(err)
			return
		}
		body := `{"client_revision":1052878631}`
		_, _ = fmt.Fprintf(tlsConn, "HTTP/1.1 200 OK\r\nContent-Length: %d\r\nConnection: close\r\n\r\n%s", len(body), body)
	}))
	t.Cleanup(proxy.Close)
	host, port, err := net.SplitHostPort(strings.TrimPrefix(proxy.URL, "http://"))
	if err != nil {
		t.Fatal(err)
	}
	dialer := &net.Dialer{}
	transport := &http.Transport{TLSClientConfig: &tls.Config{RootCAs: ca, MinVersion: tls.VersionTLS12}, DialContext: func(ctx context.Context, network, addr string) (net.Conn, error) {
		if addr == "web.whatsapp.com:443" {
			return nil, errors.New("direct access unavailable")
		}
		return dialer.DialContext(ctx, network, addr)
	}}
	return host, port, transport
}

func TestVersionLookupUsesConfiguredGlobalProxy(t *testing.T) {
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
	expectedAuth := "Basic " + base64.StdEncoding.EncodeToString([]byte("test-user:test:p@ss"))
	host, port, transport := testVersionProxy(t, expectedAuth)
	http.DefaultTransport = transport
	if err := InitializeWAVersion(&config.Config{ProxyProtocol: "http", ProxyHost: host, ProxyPort: port, ProxyUsername: "test-user", ProxyPassword: "test:p@ss"}); err != nil {
		t.Fatalf("version lookup should work through the configured proxy: %v", err)
	}
	if store.GetWAVersion() != (store.WAVersionContainer{2, 3000, 1052878631}) {
		t.Fatal("proxy revision was not applied")
	}
}

func TestBackgroundVersionLookupUsesInstanceProxy(t *testing.T) {
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
	host, port, transport := testVersionProxy(t, "")
	http.DefaultTransport = transport
	raw, err := json.Marshal(ProxyConfig{Protocol: "http", Host: host, Port: port})
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	done := make(chan struct{})
	go func() {
		retryWAVersionInitialization(ctx, &config.Config{}, func(context.Context) ([]string, error) { return []string{string(raw)}, nil }, time.Millisecond)
		close(done)
	}()
	select {
	case <-waVersionInitialization.ready:
	case <-ctx.Done():
		t.Fatal("instance proxy did not initialize the version")
	}
	<-done
	if store.GetWAVersion() != (store.WAVersionContainer{2, 3000, 1052878631}) {
		t.Fatal("instance proxy revision was not applied")
	}
}

func TestVersionLookupFailureDoesNotExposeProxyCredentials(t *testing.T) {
	oldTransport := http.DefaultTransport
	http.DefaultTransport = roundTripperFunc(func(*http.Request) (*http.Response, error) { return nil, errors.New("direct unavailable") })
	t.Cleanup(func() { http.DefaultTransport = oldTransport })
	_, err := fetchWhatsAppWebVersion(context.Background(), &config.Config{ProxyHost: "127.0.0.1", ProxyPort: "1", ProxyUsername: "private-user", ProxyPassword: "private-password"}, nil)
	if err == nil || strings.Contains(err.Error(), "private-user") || strings.Contains(err.Error(), "private-password") {
		t.Fatalf("proxy error must not expose credentials: %v", err)
	}
}
