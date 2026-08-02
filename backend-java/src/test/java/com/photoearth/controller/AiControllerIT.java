package com.photoearth.controller;

import com.anthropic.client.AnthropicClient;
import com.anthropic.models.messages.ContentBlock;
import com.anthropic.models.messages.Message;
import com.anthropic.models.messages.MessageCreateParams;
import com.anthropic.models.messages.TextBlock;
import com.anthropic.services.blocking.MessageService;
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
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import java.nio.file.Path;
import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.MOCK)
@AutoConfigureMockMvc
class AiControllerIT {

    @TempDir
    static Path tempDir;

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockitoBean
    private AnthropicClient anthropicClient;

    @DynamicPropertySource
    static void properties(DynamicPropertyRegistry registry) {
        registry.add("photoearth.db-path", () -> tempDir.resolve("ai.db").toString());
        registry.add("photoearth.upload-dir", () -> tempDir.resolve("uploads").toString());
        registry.add("photoearth.frontend-dist-path", () -> tempDir.resolve("no-frontend").toString());
    }

    private long uploadPlainPhoto() throws Exception {
        MockMultipartFile image = new MockMultipartFile(
                "files", "plain.jpg", "image/jpeg", JpegFixtures.plainJpeg());
        String response = mockMvc.perform(multipart("/api/photos/upload").file(image))
                .andReturn().getResponse().getContentAsString();
        return objectMapper.readTree(response).get(0).get("id").asLong();
    }

    private void stubAiResponse(String jsonText) {
        MessageService messageService = org.mockito.Mockito.mock(MessageService.class);
        TextBlock textBlock = org.mockito.Mockito.mock(TextBlock.class);
        when(textBlock.text()).thenReturn(jsonText);
        ContentBlock contentBlock = org.mockito.Mockito.mock(ContentBlock.class);
        when(contentBlock.asText()).thenReturn(textBlock);
        Message message = org.mockito.Mockito.mock(Message.class);
        when(message.content()).thenReturn(List.of(contentBlock));
        when(messageService.create(any(MessageCreateParams.class))).thenReturn(message);
        when(anthropicClient.messages()).thenReturn(messageService);
    }

    @Test
    void detectLocationSetsAiSourceOnSuccess() throws Exception {
        long photoId = uploadPlainPhoto();
        stubAiResponse("""
                {"lat": 47.3769, "lng": 8.5417, "location_name": "Zurich, Switzerland", \
                "confidence": "high", "reasoning": "Landmark match"}""");

        mockMvc.perform(post("/api/ai/{id}/detect-location", photoId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.location_source").value("ai"))
                .andExpect(jsonPath("$.location_name").value("Zurich, Switzerland"))
                .andExpect(jsonPath("$.lat").value(47.3769))
                .andExpect(jsonPath("$.lng").value(8.5417));
    }

    @Test
    void detectLocationReturns422WhenAiCannotLocate() throws Exception {
        long photoId = uploadPlainPhoto();
        stubAiResponse("""
                {"lat": null, "lng": null, "confidence": "low", "reasoning": "No landmarks visible"}""");

        mockMvc.perform(post("/api/ai/{id}/detect-location", photoId))
                .andExpect(status().isUnprocessableContent());
    }

    @Test
    void detectLocationReturns500OnMalformedJson() throws Exception {
        long photoId = uploadPlainPhoto();
        stubAiResponse("not json at all");

        mockMvc.perform(post("/api/ai/{id}/detect-location", photoId))
                .andExpect(status().isInternalServerError());
    }

    @Test
    void detectLocationReturns404WhenPhotoMissing() throws Exception {
        mockMvc.perform(post("/api/ai/{id}/detect-location", 999_999))
                .andExpect(status().isNotFound());
    }
}
