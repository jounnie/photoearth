package com.photoearth.service;

import com.drew.imaging.ImageMetadataReader;
import com.drew.imaging.ImageProcessingException;
import com.drew.lang.GeoLocation;
import com.drew.metadata.Metadata;
import com.drew.metadata.exif.ExifIFD0Directory;
import com.drew.metadata.exif.ExifSubIFDDirectory;
import com.drew.metadata.exif.GpsDirectory;
import org.springframework.stereotype.Service;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;

/**
 * Mirrors backend/app/exif_utils.py: DateTimeOriginal is checked first and, if present at
 * all, is never replaced by a fallback to DateTime even when it fails to parse.
 */
@Service
public class ExifExtractionService {

    private static final DateTimeFormatter EXIF_DATE_FORMAT =
            DateTimeFormatter.ofPattern("yyyy:MM:dd HH:mm:ss");

    public ExifMetadata extractMetadata(byte[] data) {
        Metadata metadata;
        try {
            metadata = ImageMetadataReader.readMetadata(new ByteArrayInputStream(data));
        } catch (ImageProcessingException | IOException e) {
            throw new RuntimeException("Failed to read image metadata", e);
        }

        Double lat = null;
        Double lng = null;
        GpsDirectory gpsDirectory = metadata.getFirstDirectoryOfType(GpsDirectory.class);
        if (gpsDirectory != null) {
            GeoLocation geoLocation = gpsDirectory.getGeoLocation();
            if (geoLocation != null) {
                lat = geoLocation.getLatitude();
                lng = geoLocation.getLongitude();
            }
        }

        LocalDateTime takenAt = null;
        ExifSubIFDDirectory subIfd = metadata.getFirstDirectoryOfType(ExifSubIFDDirectory.class);
        if (subIfd != null && subIfd.containsTag(ExifSubIFDDirectory.TAG_DATETIME_ORIGINAL)) {
            takenAt = parseExifDate(subIfd.getString(ExifSubIFDDirectory.TAG_DATETIME_ORIGINAL));
        } else {
            ExifIFD0Directory ifd0 = metadata.getFirstDirectoryOfType(ExifIFD0Directory.class);
            if (ifd0 != null && ifd0.containsTag(ExifIFD0Directory.TAG_DATETIME)) {
                takenAt = parseExifDate(ifd0.getString(ExifIFD0Directory.TAG_DATETIME));
            }
        }

        return new ExifMetadata(lat, lng, takenAt);
    }

    private LocalDateTime parseExifDate(String raw) {
        if (raw == null) {
            return null;
        }
        try {
            return LocalDateTime.parse(raw, EXIF_DATE_FORMAT);
        } catch (DateTimeParseException e) {
            return null;
        }
    }
}
