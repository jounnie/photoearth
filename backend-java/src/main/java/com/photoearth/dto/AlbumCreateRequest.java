package com.photoearth.dto;

import jakarta.validation.constraints.NotNull;

public record AlbumCreateRequest(
        @NotNull String name,
        String description
) {
    public AlbumCreateRequest {
        if (description == null) {
            description = "";
        }
    }
}
