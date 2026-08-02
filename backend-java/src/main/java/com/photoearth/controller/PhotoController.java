package com.photoearth.controller;

import com.photoearth.dto.PhotoGpsUpdateRequest;
import com.photoearth.dto.PhotoOut;
import com.photoearth.service.PhotoService;
import jakarta.validation.Valid;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.MediaTypeFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

@RestController
@RequestMapping("/api/photos")
public class PhotoController {

    private final PhotoService photoService;

    public PhotoController(PhotoService photoService) {
        this.photoService = photoService;
    }

    @GetMapping
    public List<PhotoOut> listPhotos(@RequestParam(required = false) Long albumId) {
        return photoService.list(albumId);
    }

    @PostMapping("/upload")
    public List<PhotoOut> uploadPhotos(
            @RequestParam("files") List<MultipartFile> files,
            @RequestParam(required = false) Long albumId
    ) {
        return photoService.upload(files, albumId);
    }

    @GetMapping("/{photoId}/image")
    public ResponseEntity<Resource> getImage(@PathVariable Long photoId) {
        Resource resource = new FileSystemResource(photoService.getImagePath(photoId));
        MediaType mediaType = MediaTypeFactory.getMediaType(resource).orElse(MediaType.APPLICATION_OCTET_STREAM);
        return ResponseEntity.ok().contentType(mediaType).body(resource);
    }

    @PatchMapping("/{photoId}/gps")
    public PhotoOut updateGps(@PathVariable Long photoId, @Valid @RequestBody PhotoGpsUpdateRequest body) {
        return photoService.updateGps(photoId, body);
    }

    @PatchMapping("/{photoId}/album")
    public PhotoOut assignAlbum(@PathVariable Long photoId, @RequestParam(required = false) Long albumId) {
        return photoService.assignAlbum(photoId, albumId);
    }

    @DeleteMapping("/{photoId}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void deletePhoto(@PathVariable Long photoId) {
        photoService.delete(photoId);
    }
}
