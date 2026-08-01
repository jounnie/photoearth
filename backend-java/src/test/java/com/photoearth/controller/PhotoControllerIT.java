package com.photoearth.controller;

import tools.jackson.databind.JsonNode;
import tools.jackson.databind.ObjectMapper;
import com.photoearth.support.JpegFixtures;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;

import java.nio.file.Path;

import static org.hamcrest.Matchers.hasSize;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.MOCK)
@AutoConfigureMockMvc
class PhotoControllerIT {

    @TempDir
    static Path tempDir;

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @DynamicPropertySource
    static void properties(DynamicPropertyRegistry registry) {
        registry.add("photoearth.db-path", () -> tempDir.resolve("photos.db").toString());
        registry.add("photoearth.upload-dir", () -> tempDir.resolve("uploads").toString());
        registry.add("photoearth.frontend-dist-path", () -> tempDir.resolve("no-frontend").toString());
    }

    @Test
    void uploadSkipsNonImageFilesAndExtractsGps() throws Exception {
        MockMultipartFile image = new MockMultipartFile(
                "files", "trip.jpg", "image/jpeg", JpegFixtures.jpegWithGps(47.3769, 8.5417));
        MockMultipartFile notImage = new MockMultipartFile(
                "files", "notes.txt", "text/plain", "hello".getBytes());

        mockMvc.perform(multipart("/api/photos/upload").file(image).file(notImage))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(1)))
                .andExpect(jsonPath("$[0].original_name").value("trip.jpg"))
                .andExpect(jsonPath("$[0].location_source").value("exif"))
                .andExpect(jsonPath("$[0].gps_type").value("ok"));
    }

    @Test
    void listAndGetImageAndDeleteRoundTrip() throws Exception {
        MockMultipartFile image = new MockMultipartFile(
                "files", "plain.jpg", "image/jpeg", JpegFixtures.plainJpeg());

        String uploadResponse = mockMvc.perform(multipart("/api/photos/upload").file(image))
                .andExpect(status().isOk())
                .andReturn().getResponse().getContentAsString();
        JsonNode photo = objectMapper.readTree(uploadResponse).get(0);
        long photoId = photo.get("id").asLong();

        mockMvc.perform(get("/api/photos"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].id").value(photoId));

        mockMvc.perform(get("/api/photos/{id}/image", photoId))
                .andExpect(status().isOk())
                .andExpect(content().contentType("image/jpeg"));

        mockMvc.perform(delete("/api/photos/{id}", photoId))
                .andExpect(status().isNoContent());

        mockMvc.perform(get("/api/photos/{id}/image", photoId))
                .andExpect(status().isNotFound());
    }

    @Test
    void patchGpsForcesManualSource() throws Exception {
        MockMultipartFile image = new MockMultipartFile(
                "files", "plain.jpg", "image/jpeg", JpegFixtures.plainJpeg());
        String uploadResponse = mockMvc.perform(multipart("/api/photos/upload").file(image))
                .andExpect(status().isOk())
                .andReturn().getResponse().getContentAsString();
        long photoId = objectMapper.readTree(uploadResponse).get(0).get("id").asLong();

        mockMvc.perform(patch("/api/photos/{id}/gps", photoId)
                        .contentType("application/json")
                        .content("{\"lat\": 1.5, \"lng\": 2.5, \"location_name\": \"Somewhere\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.lat").value(1.5))
                .andExpect(jsonPath("$.lng").value(2.5))
                .andExpect(jsonPath("$.location_source").value("manual"))
                .andExpect(jsonPath("$.gps_type").value("ok"));
    }

    @Test
    void gpsUpdateOnMissingPhotoReturns404() throws Exception {
        mockMvc.perform(patch("/api/photos/{id}/gps", 999_999)
                        .contentType("application/json")
                        .content("{\"lat\": 1.0, \"lng\": 2.0}"))
                .andExpect(status().isNotFound());
    }
}
