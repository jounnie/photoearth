package com.photoearth.service;

import com.photoearth.domain.Album;
import com.photoearth.dto.AlbumCreateRequest;
import com.photoearth.dto.AlbumOut;
import com.photoearth.dto.AlbumUpdateRequest;
import com.photoearth.exception.NotFoundException;
import com.photoearth.mapper.AlbumMapper;
import com.photoearth.repository.AlbumRepository;
import com.photoearth.repository.PhotoRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class AlbumService {

    private final AlbumRepository albumRepository;
    private final PhotoRepository photoRepository;
    private final AlbumMapper albumMapper;

    public AlbumService(AlbumRepository albumRepository, PhotoRepository photoRepository, AlbumMapper albumMapper) {
        this.albumRepository = albumRepository;
        this.photoRepository = photoRepository;
        this.albumMapper = albumMapper;
    }

    @Transactional(readOnly = true)
    public List<AlbumOut> list() {
        List<Album> albums = albumRepository.findAllByOrderByCreatedAtDesc();

        Map<Long, Long> counts = new HashMap<>();
        for (Object[] row : photoRepository.countGroupedByAlbumId()) {
            Long albumId = (Long) row[0];
            Long count = (Long) row[1];
            counts.put(albumId, count);
        }

        return albums.stream()
                .map(album -> albumMapper.toDto(album, counts.getOrDefault(album.getId(), 0L)))
                .toList();
    }

    @Transactional
    public AlbumOut create(AlbumCreateRequest request) {
        Album album = new Album();
        album.setName(request.name());
        album.setDescription(request.description());
        album = albumRepository.save(album);
        return albumMapper.toDto(album, 0);
    }

    @Transactional
    public AlbumOut update(Long albumId, AlbumUpdateRequest request) {
        Album album = albumRepository.findById(albumId)
                .orElseThrow(() -> new NotFoundException("Album not found"));
        if (request.name() != null) {
            album.setName(request.name());
        }
        if (request.description() != null) {
            album.setDescription(request.description());
        }
        long count = photoRepository.countByAlbumId(albumId);
        return albumMapper.toDto(album, count);
    }

    @Transactional
    public void delete(Long albumId) {
        Album album = albumRepository.findById(albumId)
                .orElseThrow(() -> new NotFoundException("Album not found"));
        // orphanRemoval=true cascades photo ROWS only — files on disk are intentionally
        // left behind, matching the Python backend's behavior.
        albumRepository.delete(album);
    }
}
