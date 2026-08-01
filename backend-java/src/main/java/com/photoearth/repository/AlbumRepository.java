package com.photoearth.repository;

import com.photoearth.domain.Album;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface AlbumRepository extends JpaRepository<Album, Long> {

    List<Album> findAllByOrderByCreatedAtDesc();
}
