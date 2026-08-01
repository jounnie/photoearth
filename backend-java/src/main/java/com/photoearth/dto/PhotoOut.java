package com.photoearth.dto;

import java.time.LocalDateTime;

public record PhotoOut(
        Long id,
        String filename,
        String originalName,
        Long albumId,
        Double exifLat,
        Double exifLng,
        Double manualLat,
        Double manualLng,
        Double lat,
        Double lng,
        String gpsType,
        String locationName,
        String locationSource,
        LocalDateTime takenAt,
        LocalDateTime uploadedAt
) {
}
