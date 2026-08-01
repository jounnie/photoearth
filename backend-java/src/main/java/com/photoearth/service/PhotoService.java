package com.photoearth.service;

import com.photoearth.domain.Album;
import com.photoearth.domain.Photo;
import com.photoearth.dto.PhotoGpsUpdateRequest;
import com.photoearth.dto.PhotoOut;
import com.photoearth.exception.NotFoundException;
import com.photoearth.mapper.PhotoMapper;
import com.photoearth.repository.AlbumRepository;
import com.photoearth.repository.PhotoRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.util.List;
import java.util.UUID;

@Service
public class PhotoService {

    private final PhotoRepository photoRepository;
    private final AlbumRepository albumRepository;
    private final FileStorageService fileStorageService;
    private final ExifExtractionService exifExtractionService;
    private final PhotoMapper photoMapper;

    public PhotoService(
            PhotoRepository photoRepository,
            AlbumRepository albumRepository,
            FileStorageService fileStorageService,
            ExifExtractionService exifExtractionService,
            PhotoMapper photoMapper
    ) {
        this.photoRepository = photoRepository;
        this.albumRepository = albumRepository;
        this.fileStorageService = fileStorageService;
        this.exifExtractionService = exifExtractionService;
        this.photoMapper = photoMapper;
    }

    @Transactional(readOnly = true)
    public List<PhotoOut> list(Long albumId) {
        List<Photo> photos = albumId != null
                ? photoRepository.findByAlbumIdOrderByUploadedAtDesc(albumId)
                : photoRepository.findAllByOrderByUploadedAtDesc();
        return photos.stream().map(photoMapper::toDto).toList();
    }

    @Transactional
    public List<PhotoOut> upload(List<MultipartFile> files, Long albumId) {
        Album album = albumId != null ? albumRepository.getReferenceById(albumId) : null;

        return files.stream()
                .map(file -> processUpload(file, album))
                .filter(java.util.Objects::nonNull)
                .map(photoRepository::save)
                .map(photoMapper::toDto)
                .toList();
    }

    private Photo processUpload(MultipartFile file, Album album) {
        String contentType = file.getContentType();
        if (contentType == null || !contentType.startsWith("image/")) {
            return null;
        }

        byte[] data;
        try {
            data = file.getBytes();
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }

        ExifMetadata meta = exifExtractionService.extractMetadata(data);

        String originalFilename = file.getOriginalFilename();
        String ext = extractExtension(originalFilename);
        String filename = UUID.randomUUID().toString().replace("-", "") + ext;
        fileStorageService.save(filename, data);

        Photo photo = new Photo();
        photo.setFilename(filename);
        photo.setOriginalName(originalFilename != null && !originalFilename.isBlank() ? originalFilename : filename);
        photo.setAlbum(album);
        photo.setExifLat(meta.lat());
        photo.setExifLng(meta.lng());
        photo.setTakenAt(meta.takenAt());
        photo.setLocationSource(meta.lat() != null ? "exif" : null);
        return photo;
    }

    private String extractExtension(String originalFilename) {
        String name = originalFilename == null || originalFilename.isBlank() ? "photo.jpg" : originalFilename;
        int dot = name.lastIndexOf('.');
        String ext = dot >= 0 ? name.substring(dot).toLowerCase() : "";
        return ext.isEmpty() ? ".jpg" : ext;
    }

    @Transactional(readOnly = true)
    public Path getImagePath(Long photoId) {
        Photo photo = photoRepository.findById(photoId)
                .orElseThrow(() -> new NotFoundException("Photo not found"));
        if (!fileStorageService.exists(photo.getFilename())) {
            throw new NotFoundException("File not found");
        }
        return fileStorageService.resolve(photo.getFilename());
    }

    @Transactional
    public PhotoOut updateGps(Long photoId, PhotoGpsUpdateRequest body) {
        Photo photo = photoRepository.findById(photoId)
                .orElseThrow(() -> new NotFoundException("Photo not found"));
        photo.setManualLat(body.lat());
        photo.setManualLng(body.lng());
        photo.setLocationName(body.locationName());
        photo.setLocationSource("manual");
        return photoMapper.toDto(photo);
    }

    @Transactional
    public PhotoOut assignAlbum(Long photoId, Long albumId) {
        Photo photo = photoRepository.findById(photoId)
                .orElseThrow(() -> new NotFoundException("Photo not found"));
        Album album = albumId != null ? albumRepository.getReferenceById(albumId) : null;
        photo.setAlbum(album);
        return photoMapper.toDto(photo);
    }

    @Transactional
    public void delete(Long photoId) {
        Photo photo = photoRepository.findById(photoId)
                .orElseThrow(() -> new NotFoundException("Photo not found"));
        fileStorageService.delete(photo.getFilename());
        photoRepository.delete(photo);
    }
}
