# SRT Metrics Reference — Haivision Makito x4 Style

## Overview

This document describes all SRT metrics collected by the Media Stream Analyzer, matching the Haivision Makito Decoder x4 statistics display.

## Connection State

| State | Description | Color |
|-------|-------------|-------|
| **STOPPED** | Connection not active | Gray |
| **CONNECTING** | Attempting to connect | Orange |
| **LISTENING** | Waiting for incoming connection | Blue |
| **STREAMING** | Active data transmission | Green |
| **BROKEN** | Connection lost/error | Red |
| **PAUSED** | Stream paused | Purple |
| **SECURING** | Encryption handshake | Yellow |
| **SCRAMBLED** | Content scrambled | Yellow |

## Network Metrics

### RTT (Round Trip Time)
- **Field**: `msRTT`
- **Unit**: milliseconds
- **Description**: Smoothed round-trip time
- **Warning threshold**: > 100ms
- **Critical threshold**: > 200ms
- **Good value**: < 50ms

### Bandwidth
- **Field**: `mbpsBandwidth`
- **Unit**: Mbps
- **Description**: Estimated available network bandwidth
- **Calculation**: Based on packet delivery rate and loss

### Receive Rate
- **Field**: `mbpsRecvRate`
- **Unit**: Mbps
- **Description**: Actual receiving bitrate
- **Note**: Should be close to stream bitrate

### Max BW Limit
- **Field**: `mbpsMaxBW`
- **Unit**: Mbps
- **Description**: Configured maximum bandwidth limit (0 = unlimited)

## Packet Statistics

### Received Packets
- **Total**: `pktRecvTotal` — All packets received (including retransmissions)
- **Unique**: `pktRecvUniqueTotal` — Unique packets (excluding retransmissions)
- **Interval**: `pktRecvUnique` — Unique packets in last interval

### Lost Packets
- **Total**: `pktRcvLossTotal`
- **Rate**: `loss_rate_percent` = (loss_total / unique_total) × 100
- **Warning**: > 1%
- **Critical**: > 5%

### Dropped Packets
- **Total**: `pktRcvDropTotal` — Packets dropped (arrived too late)
- **Undecryptable**: `pktRcvUndecryptTotal` — Failed decryption
- **Rate**: `drop_rate_percent`
- **Warning**: > 0.1%

### Retransmitted Packets
- **Total**: `pktRcvRetransTotal` — Retransmitted packets received
- **Ratio**: `retrans_ratio_percent` = (retrans / recv_total) × 100
- **Note**: High ratio indicates poor network conditions

## Buffer Metrics

### Buffer Health
- **Calculation**: `(msRcvBuf / msRcvTsbPdDelay) × 100`
- **Unit**: Percentage
- **Good**: > 80%
- **Warning**: < 50%
- **Critical**: < 20%

### Buffer Timespan
- **Field**: `msRcvBuf`
- **Unit**: milliseconds
- **Description**: Time span of packets in receiver buffer

### TSBPD Delay
- **Field**: `msRcvTsbPdDelay`
- **Unit**: milliseconds
- **Description**: Timestamp-based packet delivery delay
- **Default**: 120ms

## Congestion Metrics

### Congestion Window
- **Field**: `pktCongestionWindow`
- **Description**: Maximum packets allowed in flight

### Flight Size
- **Field**: `pktFlightSize`
- **Description**: Currently unacknowledged packets

### Reorder Tolerance
- **Field**: `pktReorderTolerance`
- **Description**: Maximum packet reordering distance accepted

## SRT Socket Options (Configuration)

| Option | Default | Description |
|--------|---------|-------------|
| `SRTO_LATENCY` | 120ms | Receiver latency |
| `SRTO_PEERLATENCY` | 0 | Sender latency (negotiated) |
| `SRTO_RCVLATENCY` | 120ms | Receiver latency override |
| `SRTO_MAXBW` | 0 | Max bandwidth (0 = unlimited) |
| `SRTO_MSS` | 1500 | Maximum segment size |
| `SRTO_RCVBUFSIZE` | 8192 | Receiver buffer size (packets) |
| `SRTO_SNDBUFSIZE` | 8192 | Sender buffer size (packets) |
| `SRTO_PASSPHRASE` | "" | Encryption passphrase |
| `SRTO_PBKEYLEN` | 0 | Encryption key length (16/24/32) |
| `SRTO_STREAMID` | "" | Stream ID for access control |

## Makito x4 Comparison

| Makito x4 Display | Our Field | Notes |
|-------------------|-----------|-------|
| Status | `connection.state` | Same states |
| Up Time | `connection.up_time` | Formatted duration |
| Source | `connection.source_address` | IP:port |
| RTT | `network.rtt_ms` | Same |
| Bandwidth | `network.bandwidth_mbps` | Same |
| Loss | `packets.loss_rate_percent` | Same |
| Drop | `packets.drop_rate_percent` | Same |
| Buffer | `buffer.health_percent` | Calculated |
| Latency | `connection.peer_latency_ms` | Same |
| Encryption | `connection.encryption` | Same |
