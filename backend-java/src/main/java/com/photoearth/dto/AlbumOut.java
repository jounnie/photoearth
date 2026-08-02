package com.photoearth.dto;

import java.time.LocalDateTime;

public record AlbumOut(
        Long id,
        String name,
        String description,
        LocalDateTime createdAt,
        long photoCount
) {
}
