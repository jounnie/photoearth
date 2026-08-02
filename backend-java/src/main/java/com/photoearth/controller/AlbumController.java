package com.photoearth.controller;

import com.photoearth.dto.AlbumCreateRequest;
import com.photoearth.dto.AlbumOut;
import com.photoearth.dto.AlbumUpdateRequest;
import com.photoearth.service.AlbumService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/albums")
public class AlbumController {

    private final AlbumService albumService;

    public AlbumController(AlbumService albumService) {
        this.albumService = albumService;
    }

    @GetMapping
    public List<AlbumOut> listAlbums() {
        return albumService.list();
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public AlbumOut createAlbum(@Valid @RequestBody AlbumCreateRequest body) {
        return albumService.create(body);
    }

    @PatchMapping("/{albumId}")
    public AlbumOut updateAlbum(@PathVariable Long albumId, @RequestBody AlbumUpdateRequest body) {
        return albumService.update(albumId, body);
    }

    @DeleteMapping("/{albumId}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void deleteAlbum(@PathVariable Long albumId) {
        albumService.delete(albumId);
    }
}
