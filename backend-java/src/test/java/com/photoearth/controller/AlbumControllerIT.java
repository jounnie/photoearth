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

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.MOCK)
@AutoConfigureMockMvc
class AlbumControllerIT {

    @TempDir
    static Path tempDir;

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @DynamicPropertySource
    static void properties(DynamicPropertyRegistry registry) {
        registry.add("photoearth.db-path", () -> tempDir.resolve("albums.db").toString());
        registry.add("photoearth.upload-dir", () -> tempDir.resolve("uploads").toString());
        registry.add("photoearth.frontend-dist-path", () -> tempDir.resolve("no-frontend").toString());
    }

    @Test
    void createDefaultsDescriptionAndPhotoCount() throws Exception {
        mockMvc.perform(post("/api/albums")
                        .contentType("application/json")
                        .content("{\"name\": \"Summer trip\"}"))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.name").value("Summer trip"))
                .andExpect(jsonPath("$.description").value(""))
                .andExpect(jsonPath("$.photo_count").value(0));
    }

    @Test
    void listReflectsAssignedPhotoCount() throws Exception {
        String albumResponse = mockMvc.perform(post("/api/albums")
                        .contentType("application/json")
                        .content("{\"name\": \"Album with photos\"}"))
                .andReturn().getResponse().getContentAsString();
        long albumId = objectMapper.readTree(albumResponse).get("id").asLong();

        MockMultipartFile image = new MockMultipartFile(
                "files", "plain.jpg", "image/jpeg", JpegFixtures.plainJpeg());
        mockMvc.perform(multipart("/api/photos/upload")
                        .file(image)
                        .param("albumId", String.valueOf(albumId)))
                .andExpect(status().isOk());

        mockMvc.perform(get("/api/albums"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].id").value(albumId))
                .andExpect(jsonPath("$[0].photo_count").value(1));
    }

    @Test
    void partialUpdateOnlyChangesProvidedFields() throws Exception {
        String albumResponse = mockMvc.perform(post("/api/albums")
                        .contentType("application/json")
                        .content("{\"name\": \"Original\", \"description\": \"Original desc\"}"))
                .andReturn().getResponse().getContentAsString();
        JsonNode created = objectMapper.readTree(albumResponse);
        long albumId = created.get("id").asLong();

        mockMvc.perform(patch("/api/albums/{id}", albumId)
                        .contentType("application/json")
                        .content("{\"name\": \"Renamed\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name").value("Renamed"))
                .andExpect(jsonPath("$.description").value("Original desc"));
    }

    @Test
    void deleteRemovesAlbum() throws Exception {
        String albumResponse = mockMvc.perform(post("/api/albums")
                        .contentType("application/json")
                        .content("{\"name\": \"To delete\"}"))
                .andReturn().getResponse().getContentAsString();
        long albumId = objectMapper.readTree(albumResponse).get("id").asLong();

        mockMvc.perform(delete("/api/albums/{id}", albumId))
                .andExpect(status().isNoContent());

        mockMvc.perform(patch("/api/albums/{id}", albumId)
                        .contentType("application/json")
                        .content("{\"name\": \"noop\"}"))
                .andExpect(status().isNotFound());
    }
}
