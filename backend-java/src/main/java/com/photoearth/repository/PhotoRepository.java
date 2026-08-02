package com.photoearth.repository;

import com.photoearth.domain.Photo;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;

public interface PhotoRepository extends JpaRepository<Photo, Long> {

    List<Photo> findAllByOrderByUploadedAtDesc();

    List<Photo> findByAlbumIdOrderByUploadedAtDesc(Long albumId);

    long countByAlbumId(Long albumId);

    @Query("select p.album.id, count(p) from Photo p group by p.album.id")
    List<Object[]> countGroupedByAlbumId();
}
