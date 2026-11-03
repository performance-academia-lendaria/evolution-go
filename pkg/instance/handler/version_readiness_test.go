package instance_handler

import (
	"errors"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	instance_model "github.com/evolution-foundation/evolution-go/pkg/instance/model"
	instance_service "github.com/evolution-foundation/evolution-go/pkg/instance/service"
	whatsmeow_service "github.com/evolution-foundation/evolution-go/pkg/whatsmeow/service"
	"github.com/gin-gonic/gin"
)

type notReadyService struct {
	instance_service.InstanceService
}

func (notReadyService) Connect(*instance_service.ConnectStruct, *instance_model.Instance) (*instance_model.Instance, string, string, error) {
	return nil, "", "", whatsmeow_service.ErrWAVersionNotReady
}

func TestConnectReportsUnavailableVersion(t *testing.T) {
	gin.SetMode(gin.TestMode)
	response := httptest.NewRecorder()
	ctx, _ := gin.CreateTestContext(response)
	ctx.Request = httptest.NewRequest(http.MethodPost, "/instance/connect", strings.NewReader(`{}`))
	ctx.Request.Header.Set("Content-Type", "application/json")
	ctx.Set("instance", &instance_model.Instance{})
	(&instanceHandler{instanceService: notReadyService{}}).Connect(ctx)
	if response.Code != http.StatusServiceUnavailable {
		t.Fatalf("expected 503 while version lookup is pending, got %d", response.Code)
	}
	if instanceErrorStatus(errors.New("other failure"), http.StatusInternalServerError) != http.StatusInternalServerError {
		t.Fatal("unrelated errors must keep their original status")
	}
}
