package com.photoearth;

import com.photoearth.config.AppProperties;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;

@SpringBootApplication
@EnableConfigurationProperties(AppProperties.class)
public class PhotoEarthApplication {

    public static void main(String[] args) {
        SpringApplication.run(PhotoEarthApplication.class, args);
    }
}
