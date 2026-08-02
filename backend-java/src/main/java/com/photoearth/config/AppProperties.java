package com.photoearth.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "photoearth")
public record AppProperties(
        String dbPath,
        String uploadDir,
        String frontendDistPath,
        Cors cors,
        Anthropic anthropic
) {

    public record Cors(String allowedOrigin) {
    }

    public record Anthropic(String apiKey, String model) {
    }
}
