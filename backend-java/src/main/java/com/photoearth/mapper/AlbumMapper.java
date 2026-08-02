package com.photoearth.mapper;

import com.photoearth.domain.Album;
import com.photoearth.dto.AlbumOut;
import org.springframework.stereotype.Component;

@Component
public class AlbumMapper {

    public AlbumOut toDto(Album album, long photoCount) {
        return new AlbumOut(
                album.getId(),
                album.getName(),
                album.getDescription(),
                album.getCreatedAt(),
                photoCount
        );
    }
}
