package com.photoearth.service;

import com.photoearth.config.AppProperties;
import jakarta.annotation.PostConstruct;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;

@Service
public class FileStorageService {

    private final Path uploadDir;

    public FileStorageService(AppProperties properties) {
        this.uploadDir = Path.of(properties.uploadDir());
    }

    @PostConstruct
    void createUploadDir() {
        try {
            Files.createDirectories(uploadDir);
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    public void save(String filename, byte[] data) {
        try {
            Files.write(resolve(filename), data);
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    public Path resolve(String filename) {
        return uploadDir.resolve(filename);
    }

    public boolean exists(String filename) {
        return Files.exists(resolve(filename));
    }

    public void delete(String filename) {
        try {
            Files.deleteIfExists(resolve(filename));
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }
}
