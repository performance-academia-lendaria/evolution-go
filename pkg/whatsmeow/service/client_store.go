package whatsmeow_service

import (
	"sync"

	"go.mau.fi/whatsmeow/store/sqlstore"
)

type deviceStoreInitializer struct {
	mu    sync.Mutex
	store *sqlstore.Container
}

func (s *deviceStoreInitializer) get(open func() (*sqlstore.Container, error)) (*sqlstore.Container, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.store == nil {
		container, err := open()
		if err != nil {
			return nil, err
		}
		s.store = container
	}
	return s.store, nil
}
