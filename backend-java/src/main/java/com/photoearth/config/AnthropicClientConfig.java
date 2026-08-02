package com.photoearth.config;

import com.anthropic.client.AnthropicClient;
import com.anthropic.client.okhttp.AnthropicOkHttpClient;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class AnthropicClientConfig {

    @Bean
    public AnthropicClient anthropicClient(AppProperties properties) {
        String apiKey = properties.anthropic().apiKey();
        if (apiKey == null || apiKey.isBlank()) {
            // Falls back to the ANTHROPIC_API_KEY environment variable, mirroring the
            // Python SDK's default anthropic.Anthropic() behavior.
            return AnthropicOkHttpClient.fromEnv();
        }
        return AnthropicOkHttpClient.builder().apiKey(apiKey).build();
    }
}
