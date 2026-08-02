package com.photoearth.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

import java.time.LocalDateTime;

@Entity
@Table(name = "photos")
public class Photo {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String filename;

    @Column(name = "original_name", nullable = false)
    private String originalName;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "album_id")
    private Album album;

    @Column(name = "exif_lat")
    private Double exifLat;

    @Column(name = "exif_lng")
    private Double exifLng;

    @Column(name = "manual_lat")
    private Double manualLat;

    @Column(name = "manual_lng")
    private Double manualLng;

    @Column(name = "location_name")
    private String locationName;

    @Column(name = "location_source")
    private String locationSource;

    @Column(name = "taken_at")
    private LocalDateTime takenAt;

    @Column(name = "uploaded_at")
    private LocalDateTime uploadedAt = LocalDateTime.now();

    public Photo() {
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getFilename() {
        return filename;
    }

    public void setFilename(String filename) {
        this.filename = filename;
    }

    public String getOriginalName() {
        return originalName;
    }

    public void setOriginalName(String originalName) {
        this.originalName = originalName;
    }

    public Album getAlbum() {
        return album;
    }

    public void setAlbum(Album album) {
        this.album = album;
    }

    public Double getExifLat() {
        return exifLat;
    }

    public void setExifLat(Double exifLat) {
        this.exifLat = exifLat;
    }

    public Double getExifLng() {
        return exifLng;
    }

    public void setExifLng(Double exifLng) {
        this.exifLng = exifLng;
    }

    public Double getManualLat() {
        return manualLat;
    }

    public void setManualLat(Double manualLat) {
        this.manualLat = manualLat;
    }

    public Double getManualLng() {
        return manualLng;
    }

    public void setManualLng(Double manualLng) {
        this.manualLng = manualLng;
    }

    public String getLocationName() {
        return locationName;
    }

    public void setLocationName(String locationName) {
        this.locationName = locationName;
    }

    public String getLocationSource() {
        return locationSource;
    }

    public void setLocationSource(String locationSource) {
        this.locationSource = locationSource;
    }

    public LocalDateTime getTakenAt() {
        return takenAt;
    }

    public void setTakenAt(LocalDateTime takenAt) {
        this.takenAt = takenAt;
    }

    public LocalDateTime getUploadedAt() {
        return uploadedAt;
    }

    public void setUploadedAt(LocalDateTime uploadedAt) {
        this.uploadedAt = uploadedAt;
    }
}
