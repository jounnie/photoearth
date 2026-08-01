package com.photoearth.service;

import com.photoearth.support.JpegFixtures;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.within;

class ExifExtractionServiceTest {

    private final ExifExtractionService service = new ExifExtractionService();

    @Test
    void noExifReturnsAllNull() throws Exception {
        ExifMetadata meta = service.extractMetadata(JpegFixtures.plainJpeg());

        assertThat(meta.lat()).isNull();
        assertThat(meta.lng()).isNull();
        assertThat(meta.takenAt()).isNull();
    }

    @Test
    void positiveGpsIsExtracted() throws Exception {
        ExifMetadata meta = service.extractMetadata(JpegFixtures.jpegWithGps(47.3769, 8.5417));

        assertThat(meta.lat()).isCloseTo(47.3769, within(0.001));
        assertThat(meta.lng()).isCloseTo(8.5417, within(0.001));
    }

    @Test
    void southAndWestCoordinatesAreNegated() throws Exception {
        ExifMetadata meta = service.extractMetadata(JpegFixtures.jpegWithGps(-33.8688, -70.6693));

        assertThat(meta.lat()).isCloseTo(-33.8688, within(0.001));
        assertThat(meta.lng()).isCloseTo(-70.6693, within(0.001));
    }

    @Test
    void dateTimeOriginalIsParsed() throws Exception {
        ExifMetadata meta = service.extractMetadata(JpegFixtures.jpegWithDateTimeOriginal("2024:06:15 10:30:00"));

        assertThat(meta.takenAt()).isEqualTo(LocalDateTime.of(2024, 6, 15, 10, 30, 0));
    }

    @Test
    void dateTimeIsUsedOnlyWhenDateTimeOriginalAbsent() throws Exception {
        ExifMetadata meta = service.extractMetadata(JpegFixtures.jpegWithDateTime("2024:01:02 03:04:05"));

        assertThat(meta.takenAt()).isEqualTo(LocalDateTime.of(2024, 1, 2, 3, 4, 5));
    }

    @Test
    void unparseableDateTimeOriginalDoesNotFallBackToDateTime() throws Exception {
        // Mirrors the Python quirk: once DateTimeOriginal is present, DateTime is never consulted,
        // even if DateTimeOriginal fails to parse.
        ExifMetadata meta = service.extractMetadata(
                // Same length as a real EXIF datetime (the tag is a fixed 20-byte ASCII field)
                // but not a valid date, so parsing fails.
                JpegFixtures.jpegWithBothDateTags("9999:99:99 99:99:99", "2024:01:02 03:04:05"));

        assertThat(meta.takenAt()).isNull();
    }
}
