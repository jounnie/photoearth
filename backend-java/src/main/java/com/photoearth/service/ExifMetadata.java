package com.photoearth.service;

import java.time.LocalDateTime;

public record ExifMetadata(Double lat, Double lng, LocalDateTime takenAt) {
}
