package com.photoearth.controller;

import com.photoearth.dto.PhotoOut;
import com.photoearth.service.AiLocationService;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/ai")
public class AiController {

    private final AiLocationService aiLocationService;

    public AiController(AiLocationService aiLocationService) {
        this.aiLocationService = aiLocationService;
    }

    @PostMapping("/{photoId}/detect-location")
    public PhotoOut detectLocation(@PathVariable Long photoId) {
        return aiLocationService.detectLocation(photoId);
    }
}
