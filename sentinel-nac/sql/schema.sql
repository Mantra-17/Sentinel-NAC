-- =============================================================
-- Sentinel-NAC: Zero-Trust Network Access Control System
-- Database Schema
-- File: sql/schema.sql
-- Purpose: Create all tables required by Sentinel-NAC
-- WARNING: For authorized lab use only.
-- =============================================================

CREATE DATABASE IF NOT EXISTS sentinel_nac
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE sentinel_nac;

-- -------------------------------------------------------------
-- Table: admins
-- Purpose: Administrator accounts for the dashboard
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS admins (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(64)  NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL COMMENT 'bcrypt hash',
    email       VARCHAR(128) NOT NULL,
    role        ENUM('superadmin','admin','viewer') NOT NULL DEFAULT 'admin',
    last_login  DATETIME     NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username)
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- Table: devices
-- Purpose: Master record of every device ever seen on the network
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS devices (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    mac_address         VARCHAR(17)  NOT NULL UNIQUE COMMENT 'Format: AA:BB:CC:DD:EE:FF',
    ip_address          VARCHAR(45)  NULL COMMENT 'Most recently seen IP (IPv4 or IPv6)',
    hostname            VARCHAR(128) NULL COMMENT 'DHCP-reported hostname if available',
    vendor              VARCHAR(128) NULL COMMENT 'OUI vendor lookup',
    probable_os         VARCHAR(64)  NULL COMMENT 'TTL-based OS inference',
    probable_device_type VARCHAR(64) NULL COMMENT 'e.g. laptop, mobile, router',
    fingerprint_confidence TINYINT UNSIGNED NULL DEFAULT 0 COMMENT '0-100 confidence score',
    status              ENUM('UNKNOWN','ALLOWED','BLOCKED','QUARANTINED')
                        NOT NULL DEFAULT 'UNKNOWN',
    first_seen          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,
    notes               TEXT         NULL,
    INDEX idx_mac       (mac_address),
    INDEX idx_status    (status),
    INDEX idx_last_seen (last_seen)
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- Table: device_events
-- Purpose: Full audit trail of every status change and detection event
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS device_events (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    mac_address VARCHAR(17)  NOT NULL,
    ip_address  VARCHAR(45)  NULL,
    event_type  ENUM(
                    'DEVICE_DISCOVERED',
                    'STATUS_CHANGED',
                    'ENFORCEMENT_STARTED',
                    'ENFORCEMENT_STOPPED',
                    'RECONNECT_BLOCKED',
                    'ADMIN_ACTION',
                    'ALERT_SENT',
                    'ERROR'
                ) NOT NULL,
    old_status  ENUM('UNKNOWN','ALLOWED','BLOCKED','QUARANTINED') NULL,
    new_status  ENUM('UNKNOWN','ALLOWED','BLOCKED','QUARANTINED') NULL,
    actor       VARCHAR(64)  NULL COMMENT 'System or admin username',
    details     TEXT         NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_mac        (mac_address),
    INDEX idx_event_type (event_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- Table: alerts
-- Purpose: Log of all alert notifications sent
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS alerts (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    mac_address VARCHAR(17)  NULL,
    alert_type  ENUM(
                    'NEW_UNKNOWN_DEVICE',
                    'BLOCKED_RECONNECT',
                    'ENFORCEMENT_FAILURE',
                    'SYSTEM_ERROR'
                ) NOT NULL,
    recipient   VARCHAR(128) NOT NULL,
    subject     VARCHAR(255) NOT NULL,
    body        TEXT         NOT NULL,
    sent_at     DATETIME     NULL COMMENT 'NULL if not yet sent / failed',
    status      ENUM('PENDING','SENT','FAILED') NOT NULL DEFAULT 'PENDING',
    error_msg   VARCHAR(512) NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_mac        (mac_address),
    INDEX idx_status     (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- Table: system_settings
-- Purpose: Key-value store for runtime-configurable settings
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS system_settings (
    setting_key     VARCHAR(64)  NOT NULL PRIMARY KEY,
    setting_value   TEXT         NOT NULL,
    description     VARCHAR(255) NULL,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Default settings
INSERT INTO system_settings (setting_key, setting_value, description) VALUES
    ('default_new_device_status', 'QUARANTINED',  'Status assigned to newly discovered devices'),
    ('alert_email_enabled',       '1',            'Enable/disable email alerts (1=on, 0=off)'),
    ('alert_email_recipient',     'admin@lab.local', 'Default alert recipient email'),
    ('enforcement_mode',          'simulation',   'simulation | firewall | denylist'),
    ('scan_interval_seconds',     '10',           'How often the scanner runs a full sweep (ARP)'),
    ('report_retention_days',     '90',           'How many days of events to include in reports')
ON DUPLICATE KEY UPDATE setting_key = setting_key;
