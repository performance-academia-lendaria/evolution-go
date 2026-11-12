package whatsmeow_service

import (
	"errors"
	"sync"
	"sync/atomic"
	"testing"

	"go.mau.fi/whatsmeow/store/sqlstore"
)

func TestDeviceStoreUpgradeRunsOnceAcrossConcurrentStarts(t *testing.T) {
	var initializer deviceStoreInitializer
	var opened atomic.Int32
	container := &sqlstore.Container{}
	var wg sync.WaitGroup
	start := make(chan struct{})
	for range 20 {
		wg.Go(func() {
			<-start
			got, err := initializer.get(func() (*sqlstore.Container, error) {
				opened.Add(1)
				return container, nil
			})
			if err != nil || got != container {
				t.Errorf("store not shared: %p, %v", got, err)
			}
		})
	}
	close(start)
	wg.Wait()
	if opened.Load() != 1 {
		t.Fatalf("expected one database upgrade, got %d", opened.Load())
	}
}

func TestDeviceStoreInitializationCanRetryAfterFailure(t *testing.T) {
	var initializer deviceStoreInitializer
	wantErr := errors.New("temporary database failure")
	if _, err := initializer.get(func() (*sqlstore.Container, error) { return nil, wantErr }); !errors.Is(err, wantErr) {
		t.Fatal("initialization error was lost")
	}
	container := &sqlstore.Container{}
	got, err := initializer.get(func() (*sqlstore.Container, error) { return container, nil })
	if err != nil || got != container {
		t.Fatal("a transient failure permanently disabled device storage")
	}
}

func TestDeviceStoreIsReusedAcrossSequentialReconnects(t *testing.T) {
	var initializer deviceStoreInitializer
	opened := 0
	var first *sqlstore.Container
	for cycle := range 21 { // Initial connection, then twenty reconnects.
		got, err := initializer.get(func() (*sqlstore.Container, error) {
			opened++
			return &sqlstore.Container{}, nil
		})
		if err != nil {
			t.Fatal(err)
		}
		if cycle == 0 {
			first = got
		}
		if got != first {
			t.Fatalf("reconnect %d created another device store", cycle)
		}
	}
	if opened != 1 {
		t.Fatalf("expected one auth pool across twenty reconnects, opened %d", opened)
	}
}
