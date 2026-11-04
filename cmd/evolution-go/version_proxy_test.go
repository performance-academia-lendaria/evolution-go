package main

import (
	"context"
	"reflect"
	"testing"

	"github.com/DATA-DOG/go-sqlmock"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

func TestLoadInstanceProxies(t *testing.T) {
	sqlDB, mock, err := sqlmock.New()
	if err != nil {
		t.Fatal(err)
	}
	defer sqlDB.Close()
	db, err := gorm.Open(postgres.New(postgres.Config{Conn: sqlDB}), &gorm.Config{})
	if err != nil {
		t.Fatal(err)
	}
	want := []string{`{"host":"proxy.test","port":"8080"}`}
	mock.ExpectQuery(`SELECT DISTINCT "proxy" FROM "instances" WHERE proxy <> \$1 AND proxy <> \$2`).WithArgs("", "null").WillReturnRows(sqlmock.NewRows([]string{"proxy"}).AddRow(want[0]))
	got, err := loadInstanceProxies(context.Background(), db)
	if err != nil {
		t.Fatal(err)
	}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("proxy records were not returned")
	}
	if err := mock.ExpectationsWereMet(); err != nil {
		t.Fatal(err)
	}
}
