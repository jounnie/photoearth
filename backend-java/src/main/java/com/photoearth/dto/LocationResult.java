package com.photoearth.dto;

public record LocationResult(
        Double lat,
        Double lng,
        String locationName,
        String confidence,
        String reasoning
) {
}
