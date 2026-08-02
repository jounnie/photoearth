package com.photoearth.dto;

import jakarta.validation.constraints.NotNull;

public record PhotoGpsUpdateRequest(
        @NotNull Double lat,
        @NotNull Double lng,
        String locationName
) {
}
