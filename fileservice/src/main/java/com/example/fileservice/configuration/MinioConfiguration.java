package com.example.fileservice.configuration;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Configuration
@ConfigurationProperties(prefix = "minio")
public class MinioConfiguration {

    private String endpoint;

    private Integer port;

    private String username;

    private String password;

    private Boolean skiptls;

    private String bucketname;
}
