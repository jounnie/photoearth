package com.photoearth.mapper;

import com.photoearth.domain.Photo;
import com.photoearth.dto.PhotoOut;
import org.springframework.stereotype.Component;

@Component
public class PhotoMapper {

    public PhotoOut toDto(Photo photo) {
        Double lat = photo.getManualLat() != null ? photo.getManualLat() : photo.getExifLat();
        Double lng = photo.getManualLng() != null ? photo.getManualLng() : photo.getExifLng();

        return new PhotoOut(
                photo.getId(),
                photo.getFilename(),
                photo.getOriginalName(),
                photo.getAlbum() != null ? photo.getAlbum().getId() : null,
                photo.getExifLat(),
                photo.getExifLng(),
                photo.getManualLat(),
                photo.getManualLng(),
                lat,
                lng,
                gpsType(lat, lng),
                photo.getLocationName(),
                photo.getLocationSource(),
                photo.getTakenAt(),
                photo.getUploadedAt()
        );
    }

    private String gpsType(Double lat, Double lng) {
        if (lat == null) {
            return "none";
        }
        if (lat == 0.0 && lng == 0.0) {
            return "zero";
        }
        return "ok";
    }
}
