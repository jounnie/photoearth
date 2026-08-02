package com.photoearth.service;

import com.anthropic.client.AnthropicClient;
import com.anthropic.models.messages.Base64ImageSource;
import com.anthropic.models.messages.ContentBlockParam;
import com.anthropic.models.messages.ImageBlockParam;
import com.anthropic.models.messages.Message;
import com.anthropic.models.messages.MessageCreateParams;
import com.anthropic.models.messages.Model;
import com.anthropic.models.messages.TextBlockParam;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.json.JsonMapper;
import com.photoearth.config.AppProperties;
import com.photoearth.domain.Photo;
import com.photoearth.dto.LocationResult;
import com.photoearth.dto.PhotoOut;
import com.photoearth.exception.AiNoLocationException;
import com.photoearth.exception.AiParseException;
import com.photoearth.exception.NotFoundException;
import com.photoearth.mapper.PhotoMapper;
import com.photoearth.repository.PhotoRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.List;
import java.util.Locale;
import java.util.Map;

@Service
public class AiLocationService {

    private static final String PROMPT = """
            Analyze this photo and determine where it was taken. \
            Respond ONLY with a JSON object (no markdown, no explanation) with these fields:
            {"lat": <decimal latitude>, "lng": <decimal longitude>, \
            "location_name": "<City, Country>", \
            "confidence": "<high|medium|low>", \
            "reasoning": "<one sentence why>"}
            If you cannot determine the location at all, set lat and lng to null.""";

    private static final Map<String, Base64ImageSource.MediaType> MEDIA_TYPES = Map.of(
            ".jpg", Base64ImageSource.MediaType.IMAGE_JPEG,
            ".jpeg", Base64ImageSource.MediaType.IMAGE_JPEG,
            ".png", Base64ImageSource.MediaType.IMAGE_PNG,
            ".webp", Base64ImageSource.MediaType.IMAGE_WEBP,
            ".gif", Base64ImageSource.MediaType.IMAGE_GIF
    );

    private final PhotoRepository photoRepository;
    private final FileStorageService fileStorageService;
    private final PhotoMapper photoMapper;
    private final AnthropicClient anthropicClient;
    private final AppProperties properties;
    private final ObjectMapper jsonMapper = JsonMapper.builder()
            .propertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE)
            .build();

    public AiLocationService(
            PhotoRepository photoRepository,
            FileStorageService fileStorageService,
            PhotoMapper photoMapper,
            AnthropicClient anthropicClient,
            AppProperties properties
    ) {
        this.photoRepository = photoRepository;
        this.fileStorageService = fileStorageService;
        this.photoMapper = photoMapper;
        this.anthropicClient = anthropicClient;
        this.properties = properties;
    }

    @Transactional
    public PhotoOut detectLocation(Long photoId) {
        Photo photo = photoRepository.findById(photoId)
                .orElseThrow(() -> new NotFoundException("Photo not found"));

        if (!fileStorageService.exists(photo.getFilename())) {
            throw new NotFoundException("Image file not found");
        }

        Path path = fileStorageService.resolve(photo.getFilename());
        byte[] imageBytes;
        try {
            imageBytes = Files.readAllBytes(path);
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
        String base64Data = Base64.getEncoder().encodeToString(imageBytes);
        Base64ImageSource.MediaType mediaType = mediaTypeFor(photo.getFilename());

        MessageCreateParams params = MessageCreateParams.builder()
                .model(Model.of(properties.anthropic().model()))
                .maxTokens(1024)
                .addUserMessageOfBlockParams(List.of(
                        ContentBlockParam.ofImage(ImageBlockParam.builder()
                                .source(Base64ImageSource.builder()
                                        .data(base64Data)
                                        .mediaType(mediaType)
                                        .build())
                                .build()),
                        ContentBlockParam.ofText(TextBlockParam.builder()
                                .text(PROMPT)
                                .build())
                ))
                .build();

        Message message = anthropicClient.messages().create(params);
        String responseText = message.content().get(0).asText().text();

        LocationResult result;
        try {
            result = jsonMapper.readValue(responseText, LocationResult.class);
        } catch (IOException e) {
            throw new AiParseException("Failed to parse AI response: " + e.getMessage());
        }

        if (result.lat() == null || result.lng() == null) {
            throw new AiNoLocationException("Could not determine location from image");
        }

        photo.setManualLat(result.lat());
        photo.setManualLng(result.lng());
        photo.setLocationName(result.locationName());
        photo.setLocationSource("ai");
        return photoMapper.toDto(photo);
    }

    private Base64ImageSource.MediaType mediaTypeFor(String filename) {
        int dot = filename.lastIndexOf('.');
        String ext = dot >= 0 ? filename.substring(dot).toLowerCase(Locale.ROOT) : "";
        return MEDIA_TYPES.getOrDefault(ext, Base64ImageSource.MediaType.IMAGE_JPEG);
    }
}
